"""Runtime DataHub lineage emission helpers.

This module provides runtime-only DataHub lineage primitives used by workers
to emit DataProcessInstance events and resolve stage runtime config from
DataHub metadata.
"""

import logging
import os
import time
import uuid
from dataclasses import dataclass

import requests
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.graph.client import DataHubGraph, DatahubClientConfig
from datahub.metadata.com.linkedin.pegasus2avro.dataprocess import (
    DataProcessInstanceInput,
    DataProcessInstanceOutput,
)
from datahub.metadata.schema_classes import (
    AuditStampClass,
    ChangeTypeClass,
    DataJobInfoClass,
    DataProcessInstancePropertiesClass,
    DataProcessInstanceRelationshipsClass,
    DataProcessInstanceRunEventClass,
    DataProcessRunStatusClass,
    EdgeClass,
)
from datahub.metadata.urns import DatasetUrn

from pipeline_common.lineage.contracts import DataHubDataJobKey, DatasetPlatform, ResolvedDataHubFlowConfig
from pipeline_common.lineage.urns import DataHubUrnFactory

from .contracts import DataHubLineageRuntimeConfig, DataHubRuntimeConnectionSettings, RunSpec

logger = logging.getLogger(__name__)
DEFAULT_ACTOR_URN = "urn:li:corpuser:datahub"

@dataclass(frozen=True)
class ActiveRunContext:
    run: RunSpec
    datajob_urn: str


class DataProcessInstanceMcpBuilder:
    """Build DataProcessInstance aspects and MCP payloads.

    MCP means Metadata Change Proposal in DataHub: one emitted metadata change
    for one entity URN/aspect pair. This is different from the AI ecosystem
    acronym MCP (Model Context Protocol).

    This builder converts one runtime run payload into the set of ordered MCPs
    required to upsert DataProcessInstance properties, relationships, IO edges,
    and one run-event status update.

    Emitted MCPs (ordered):
    1. `DataProcessInstancePropertiesClass`: run metadata and custom properties.
    2. `dataProcessInstanceRelationships`: link to parent DataJob template URN.
    3. `dataProcessInstanceInput`: input dataset lineage edges.
    4. `dataProcessInstanceOutput`: output dataset lineage edges.
    5. `dataProcessInstanceRunEvent`: timestamped lifecycle status event.

    Args:
        dpi_urn: DataProcessInstance URN for the current run.
        datajob_urn: Parent DataJob template URN.
        run: Runtime run payload containing run id, io sets, and metadata.
        now_ms: Event timestamp in milliseconds.
        status: Run status to emit for this event.
    """

    def __init__(
        self,
        *,
        dpi_urn: str,
        datajob_urn: str,
        run: RunSpec,
        now_ms: int,
        status: DataProcessRunStatusClass,
    ) -> None:
        """Initialize builder context for one DataProcessInstance event."""
        self.dpi_urn = dpi_urn
        self.datajob_urn = datajob_urn
        self.run = run
        self.now_ms = now_ms
        self.status = status
        self.dpi_properties_aspect: DataProcessInstancePropertiesClass | None = None
        self.dpi_relationships_aspect: DataProcessInstanceRelationshipsClass | None = None
        self.dpi_input_aspect: DataProcessInstanceInput | None = None
        self.dpi_output_aspect: DataProcessInstanceOutput | None = None
        self.dpi_run_event_aspect: DataProcessInstanceRunEventClass | None = None

    def build(self) -> list[MetadataChangeProposalWrapper]:
        """Build ordered DataProcessInstance MCPs for one run status transition.

        Returns:
            Ordered list of MetadataChangeProposalWrapper objects for one event.
        """
        self.dpi_properties_aspect = self._build_dpi_properties_aspect()
        self.dpi_relationships_aspect = self._build_dpi_relationships_aspect()
        self.dpi_input_aspect = self._build_dpi_input_aspect()
        self.dpi_output_aspect = self._build_dpi_output_aspect()
        self.dpi_run_event_aspect = self._build_dpi_run_event_aspect()
        return self._build_dpi_mcp_batch()

    def _build_dpi_properties_aspect(self) -> DataProcessInstancePropertiesClass:
        """Build `DataProcessInstancePropertiesClass` aspect payload."""
        return DataProcessInstancePropertiesClass(
            name=self.run.run_id,
            created=AuditStampClass(time=self.now_ms, actor=DEFAULT_ACTOR_URN),
            type="BATCH_SCHEDULED",
            customProperties={
                "job_version": self.run.job_version,
            },
        )

    def _build_dpi_relationships_aspect(self) -> DataProcessInstanceRelationshipsClass:
        """Build `DataProcessInstanceRelationshipsClass` aspect payload."""
        return DataProcessInstanceRelationshipsClass(upstreamInstances=[], parentTemplate=self.datajob_urn)

    def _build_dpi_input_aspect(self) -> DataProcessInstanceInput:
        """Build `DataProcessInstanceInput` aspect payload."""
        return DataProcessInstanceInput(
            inputs=[],
            inputEdges=[EdgeClass(destinationUrn=urn) for urn in self.run.inputs],
        )

    def _build_dpi_output_aspect(self) -> DataProcessInstanceOutput:
        """Build `DataProcessInstanceOutput` aspect payload."""
        return DataProcessInstanceOutput(
            outputs=[],
            outputEdges=[EdgeClass(destinationUrn=urn) for urn in self.run.outputs],
        )

    def _build_dpi_run_event_aspect(self) -> DataProcessInstanceRunEventClass:
        """Build `DataProcessInstanceRunEventClass` aspect payload."""
        return DataProcessInstanceRunEventClass(
            timestampMillis=self.now_ms,
            status=self.status,
            attempt=1,
        )

    def _build_dpi_mcp_batch(self) -> list[MetadataChangeProposalWrapper]:
        """Wrap built aspects into ordered `MetadataChangeProposalWrapper` MCPs."""
        aspect_params: list[dict[str, object]] = [
            {"aspect": self.dpi_properties_aspect},
            {
                "entityType": "dataProcessInstance",
                "aspectName": "dataProcessInstanceRelationships",
                "aspect": self.dpi_relationships_aspect,
            },
            {
                "entityType": "dataProcessInstance",
                "aspectName": "dataProcessInstanceInput",
                "aspect": self.dpi_input_aspect,
            },
            {
                "entityType": "dataProcessInstance",
                "aspectName": "dataProcessInstanceOutput",
                "aspect": self.dpi_output_aspect,
            },
            {
                "entityType": "dataProcessInstance",
                "aspectName": "dataProcessInstanceRunEvent",
                "aspect": self.dpi_run_event_aspect,
            },
        ]
        return [
            MetadataChangeProposalWrapper(
                entityUrn=self.dpi_urn,
                changeType=ChangeTypeClass.UPSERT,
                **params,
            )
            for params in aspect_params
        ]


class DataHubGraphClient:
    """Handle aspect reads and MCP writes via DataHub graph client."""

    def __init__(self, *, connection_settings: DataHubRuntimeConnectionSettings) -> None:
        """Initialize graph client from runtime connection settings."""
        self.graph = DataHubGraph(
            DatahubClientConfig(
                server=connection_settings.server,
                token=connection_settings.token,
                timeout_sec=connection_settings.timeout_sec,
                retry_max_times=connection_settings.retry_max_times,
            )
        )

    def get_datajob_info(self, job_urn: str) -> DataJobInfoClass | None:
        """Fetch the `DataJobInfo` aspect for a DataJob URN.

        Args:
            job_urn: DataJob URN to query.

        Returns:
            `DataJobInfoClass` when available; otherwise `None` on missing data
            or recoverable read errors.
        """
        try:
            with self.graph:
                return self.graph.get_aspect(job_urn, DataJobInfoClass)
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            logger.warning("Could not read DataJobInfo for %s: %s", job_urn, exc)
            return None

    def emit_mcps(self, *, mcps: list[MetadataChangeProposalWrapper]) -> None:
        """Emit MCPs to DataHub Graph in the provided order.

        Args:
            mcps: Ordered metadata change proposals to emit.
        """
        with self.graph:
            for mcp in mcps:
                self.graph.emit(mcp)


class DataHubJobMetadataResolver:
    """Retrieve static DataJob details specified by governance definitions."""

    def __init__(self, *, graph_client: DataHubGraphClient, env: str, data_job_key: DataHubDataJobKey) -> None:
        self.graph_client = graph_client
        self.env = env
        self.data_job_key = data_job_key
        self.resolved_job_config = self._resolve_job_config()

    def _resolve_job_config(self) -> ResolvedDataHubFlowConfig:
        input_job_urn = self._build_input_job_urn()
        custom_properties = self._resolve_datajob_custom_properties(input_job_urn)
        return self._build_resolved_job_config(custom_properties)

    def _build_input_job_urn(self) -> str:
        return DataHubUrnFactory.job_urn(
            flow_platform=self.data_job_key.flow_platform,
            flow_id=self.data_job_key.flow_id,
            flow_instance=self.env,
            job_id=self.data_job_key.job_id,
        )

    def _resolve_datajob_custom_properties(self, input_job_urn: str) -> dict[str, str]:
        job_info = self.graph_client.get_datajob_info(input_job_urn)
        if job_info is None or not isinstance(job_info.customProperties, dict):
            return {}
        custom_properties: dict[str, str] = {str(k): str(v) for k, v in job_info.customProperties.items()}
        return custom_properties

    def _build_resolved_job_config(self, custom_properties: dict[str, str]) -> ResolvedDataHubFlowConfig:
        return ResolvedDataHubFlowConfig(
            flow_id=self.data_job_key.flow_id,
            job_id=self.data_job_key.job_id,
            flow_platform=self.data_job_key.flow_platform,
            flow_instance=self.env,
            custom_properties=custom_properties,
        )

class DataHubRunTimeLineage:
    """Push DataProcessInstance lineage inputs/outputs and run events."""

    def __init__(self, *, client_config: DataHubLineageRuntimeConfig) -> None:
        self.graph_client = DataHubGraphClient(connection_settings=client_config.connection_settings)
        env = client_config.connection_settings.env
        resolver = DataHubJobMetadataResolver(
            graph_client=self.graph_client,
            env=env,
            data_job_key=client_config.data_job_key,
        )
        self.resolved_job_config = resolver.resolved_job_config
        self.datajob_urn = self.resolved_job_config.job_urn()
        self.job_version = self._resolve_job_version()
        self._active_context: ActiveRunContext | None = None

    def dataset_urn(self, *, platform: DatasetPlatform, name: str) -> DatasetUrn:
        return DataHubUrnFactory.dataset_urn(
            platform=platform.platform,
            name=name,
            env=self.resolved_job_config.flow_instance,
        )

    def reset_run_state(self) -> None:
        self._clear_active_run()

    def start_run(self) -> RunSpec:
        self.reset_run_state()
        run = RunSpec(
            run_id=self._generate_run_id(),
            job_version=self.job_version,
            inputs=[],
            outputs=[],
        )
        self._active_context = ActiveRunContext(
            run=run,
            datajob_urn=self.datajob_urn,
        )
        try:
            self._emit_run_status(
                datajob_urn=self.datajob_urn,
                run=run,
                status=DataProcessRunStatusClass.STARTED,
            )
        except Exception:
            self._clear_active_run()
            raise
        return run

    def add_input(self, *, name: str, platform: DatasetPlatform) -> DatasetUrn:
        dataset = self.dataset_urn(platform=platform, name=name)
        self._active_context.run.inputs.append(str(dataset))
        return dataset

    def add_output(self, *, name: str, platform: DatasetPlatform) -> DatasetUrn:
        dataset = self.dataset_urn(platform=platform, name=name)
        self._active_context.run.outputs.append(str(dataset))
        return dataset

    def _generate_run_id(self) -> str:
        return f"{int(time.time() * 1000)}-{self.resolved_job_config.job_id}-{uuid.uuid4()}"

    def emit_dpi(
        self,
        *,
        datajob_urn: str,
        run: RunSpec,
    ) -> str:
        self._emit_run_status(
            datajob_urn=datajob_urn,
            run=run,
            status=DataProcessRunStatusClass.STARTED,
        )
        self._emit_run_status(
            datajob_urn=datajob_urn,
            run=run,
            status=DataProcessRunStatusClass.COMPLETE,
        )
        return self._dpi_urn(run.run_id)

    def complete_run(self) -> str:
        if self._active_context is None:
            raise ValueError("No active run; call start_run() before complete_run().")
        context = self._active_context
        run = context.run
        completed_run = RunSpec(
            run_id=run.run_id,
            job_version=run.job_version,
            inputs=list(run.inputs),
            outputs=list(run.outputs),
        )
        self._emit_run_status(
            datajob_urn=context.datajob_urn,
            run=completed_run,
            status=DataProcessRunStatusClass.COMPLETE,
        )
        self._clear_active_run()
        return self._dpi_urn(completed_run.run_id)

    def fail_run(self, error_message: str | None) -> str:
        _ = error_message
        if self._active_context is None:
            raise ValueError("No active run; call start_run() before fail_run().")
        context = self._active_context
        run = context.run
        failed_run = RunSpec(
            run_id=run.run_id,
            job_version=run.job_version,
            inputs=list(run.inputs),
            outputs=list(run.outputs),
        )
        self._emit_run_status(
            datajob_urn=context.datajob_urn,
            run=failed_run,
            status=DataProcessRunStatusClass.FAILURE,
        )
        self._clear_active_run()
        return self._dpi_urn(failed_run.run_id)

    def abort_run(self) -> None:
        self._clear_active_run()

    def _resolve_job_version(self) -> str:
        if value := self.resolved_job_config.custom_properties.get("job.version"):
            return str(value)
        return "unknown"

    def emit_dpi_event(
        self,
        *,
        datajob_urn: str,
        run: RunSpec,
        status: DataProcessRunStatusClass,
    ) -> str:
        dpi_urn = self._dpi_urn(run.run_id)
        mcps = DataProcessInstanceMcpBuilder(
            dpi_urn=dpi_urn,
            datajob_urn=datajob_urn,
            run=run,
            now_ms=self._now_ms(),
            status=status,
        ).build()
        self.graph_client.emit_mcps(mcps=mcps)
        return dpi_urn

    def _emit_run_status(
        self,
        *,
        datajob_urn: str,
        run: RunSpec,
        status: DataProcessRunStatusClass,
    ) -> str:
        return self.emit_dpi_event(
            datajob_urn=datajob_urn,
            run=run,
            status=status,
        )

    def _dpi_urn(self, run_id: str) -> str:
        return DataHubUrnFactory.data_process_instance_urn(run_id=run_id)

    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def _clear_active_run(self) -> None:
        self._active_context = None
