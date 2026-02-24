import logging
import os
import subprocess
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
from datahub.sdk import DataHubClient as DataHubSdkClient

from pipeline_common.lineage.contracts import DataHubDataJobKey, ResolvedDataHubFlowConfig
from pipeline_common.lineage.urns import DataHubUrnFactory

from .contracts import DataHubLineageRuntimeConfig, RunSpec

logger = logging.getLogger(__name__)
DEFAULT_ACTOR_URN = "urn:li:corpuser:datahub"


@dataclass(frozen=True)
class ActiveRunContext:
    run: RunSpec
    datajob_urn: str
    external_url: str | None
    actor_urn: str


class DataProcessInstanceMcpBuilder:
    """Build DataProcessInstance aspects and MCPs from one run payload."""

    def build(
        self,
        *,
        dpi_urn: str,
        datajob_urn: str,
        run: RunSpec,
        now_ms: int,
        status: DataProcessRunStatusClass,
        actor_urn: str,
        external_url: str | None,
    ) -> list[MetadataChangeProposalWrapper]:
        properties = self._build_properties(run=run, now_ms=now_ms, actor_urn=actor_urn, external_url=external_url)
        relationships = self._build_relationships(datajob_urn=datajob_urn)
        dpi_input, dpi_output = self._build_io(run=run)
        run_event = self._build_run_event(run=run, now_ms=now_ms, status=status)
        return self._build_mcps(
            dpi_urn=dpi_urn,
            properties=properties,
            relationships=relationships,
            dpi_input=dpi_input,
            dpi_output=dpi_output,
            run_event=run_event,
        )

    def _build_properties(
        self,
        *,
        run: RunSpec,
        now_ms: int,
        actor_urn: str,
        external_url: str | None,
    ) -> DataProcessInstancePropertiesClass:
        return DataProcessInstancePropertiesClass(
            name=run.run_id,
            created=AuditStampClass(time=now_ms, actor=actor_urn),
            type="BATCH_SCHEDULED",
            externalUrl=external_url,
            customProperties={
                "job_version": run.job_version,
                "attempt": str(run.attempt),
            },
        )

    def _build_relationships(self, *, datajob_urn: str) -> DataProcessInstanceRelationshipsClass:
        return DataProcessInstanceRelationshipsClass(upstreamInstances=[], parentTemplate=datajob_urn)

    def _build_io(self, *, run: RunSpec) -> tuple[DataProcessInstanceInput, DataProcessInstanceOutput]:
        dpi_in = DataProcessInstanceInput(
            inputs=[],
            inputEdges=[EdgeClass(destinationUrn=urn) for urn in run.inputs],
        )
        dpi_out = DataProcessInstanceOutput(
            outputs=[],
            outputEdges=[EdgeClass(destinationUrn=urn) for urn in run.outputs],
        )
        return dpi_in, dpi_out

    def _build_run_event(
        self, *, run: RunSpec, now_ms: int, status: DataProcessRunStatusClass
    ) -> DataProcessInstanceRunEventClass:
        return DataProcessInstanceRunEventClass(
            timestampMillis=now_ms,
            status=status,
            attempt=run.attempt,
        )

    def _build_mcps(
        self,
        *,
        dpi_urn: str,
        properties: DataProcessInstancePropertiesClass,
        relationships: DataProcessInstanceRelationshipsClass,
        dpi_input: DataProcessInstanceInput,
        dpi_output: DataProcessInstanceOutput,
        run_event: DataProcessInstanceRunEventClass,
    ) -> list[MetadataChangeProposalWrapper]:
        return [
            MetadataChangeProposalWrapper(entityUrn=dpi_urn, aspect=properties, changeType=ChangeTypeClass.UPSERT),
            MetadataChangeProposalWrapper(
                entityUrn=dpi_urn,
                entityType="dataProcessInstance",
                aspectName="dataProcessInstanceRelationships",
                aspect=relationships,
                changeType=ChangeTypeClass.UPSERT,
            ),
            MetadataChangeProposalWrapper(
                entityUrn=dpi_urn,
                entityType="dataProcessInstance",
                aspectName="dataProcessInstanceInput",
                aspect=dpi_input,
                changeType=ChangeTypeClass.UPSERT,
            ),
            MetadataChangeProposalWrapper(
                entityUrn=dpi_urn,
                entityType="dataProcessInstance",
                aspectName="dataProcessInstanceOutput",
                aspect=dpi_output,
                changeType=ChangeTypeClass.UPSERT,
            ),
            MetadataChangeProposalWrapper(
                entityUrn=dpi_urn,
                entityType="dataProcessInstance",
                aspectName="dataProcessInstanceRunEvent",
                aspect=run_event,
                changeType=ChangeTypeClass.UPSERT,
            ),
        ]


class DataHubClient:
    """Client responsible for low-level interactions with DataHub."""

    def __init__(self, *, bootstrap_settings: dict[str, object]) -> None:
        self.server = str(bootstrap_settings["server"])
        self.env = str(bootstrap_settings["env"])
        token_value = bootstrap_settings.get("token")
        self.token = str(token_value) if token_value else None
        self.client = DataHubSdkClient(server=self.server, token=self.token)
        graph_timeout_sec = float(os.getenv("DATAHUB_TIMEOUT_SEC", "3"))
        self.graph = DataHubGraph(
            DatahubClientConfig(
                server=self.server,
                token=self.token,
                timeout_sec=graph_timeout_sec,
                retry_max_times=1,
            )
        )

    def dataset_urn(self, *, platform: str, name: str, env: str | None = None) -> DatasetUrn:
        """Build DatasetUrn with this runtime env as fallback."""
        return DataHubUrnFactory.dataset_urn(platform=platform, name=name, env=env or self.env)

    def gql_scroll(self, urn: str, direction: str, count: int = 200) -> list[str]:
        """Query lineage traversal for one entity and return connected URNs."""
        normalized_direction = direction.strip().lower()
        if normalized_direction not in {"upstream", "downstream"}:
            raise ValueError("direction must be either 'UPSTREAM'/'upstream' or 'DOWNSTREAM'/'downstream'")
        results = self.client.lineage.get_lineage(
            source_urn=urn,
            direction=normalized_direction,
            max_hops=1,
            count=count,
        )
        return [result.urn for result in results]

    def get_datajob_info(self, job_urn: str) -> DataJobInfoClass | None:
        """Read DataJobInfo aspect for one job URN from DataHub."""
        try:
            with self.graph:
                return self.graph.get_aspect(job_urn, DataJobInfoClass)
        except (requests.RequestException, RuntimeError, ValueError) as exc:
            logger.warning("Could not read DataJobInfo for %s: %s", job_urn, exc)
            return None

    def emit_mcps(self, *, mcps: list[MetadataChangeProposalWrapper]) -> None:
        """Emit MCPs to DataHub graph client in order."""
        with self.graph:
            for mcp in mcps:
                self.graph.emit(mcp)

class DataHubStaticLineage:
    """Retrieve static DataJob details specified by governance definitions."""

    def __init__(self, *, client: DataHubClient, data_job_key: DataHubDataJobKey) -> None:
        self.client = client
        self.env = client.env
        self.data_job_key = data_job_key
        self.input_flow_urn = self._build_input_flow_urn()
        self.input_job_urn = self._build_input_job_urn()
        self.stage_config = self._resolve_stage_config()

    @property
    def flow_urn(self) -> str:
        return self.stage_config.flow_urn(self.env)

    @property
    def job_urn(self) -> str:
        return self.stage_config.job_urn(self.env)

    def _build_input_flow_urn(self) -> str:
        return DataHubUrnFactory.flow_urn(
            flow_platform=self.data_job_key.flow_platform,
            flow_name=self.data_job_key.flow_id,
            flow_instance=self.env,
        )

    def _build_input_job_urn(self) -> str:
        return DataHubUrnFactory.job_urn(
            flow_platform=self.data_job_key.flow_platform,
            flow_name=self.data_job_key.flow_id,
            flow_instance=self.env,
            job_name=self.data_job_key.job_id,
        )

    def _resolve_stage_config(self) -> ResolvedDataHubFlowConfig:
        job_info = self.client.get_datajob_info(self.input_job_urn)
        custom_properties: dict[str, str] = {}
        if job_info is not None and isinstance(job_info.customProperties, dict):
            custom_properties = {str(k): str(v) for k, v in job_info.customProperties.items()}
        return ResolvedDataHubFlowConfig(
            flow_id=self.data_job_key.flow_id,
            job_id=self.data_job_key.job_id,
            flow_platform=self.data_job_key.flow_platform,
            flow_name=self.data_job_key.flow_id,
            flow_instance=self.env,
            job_name=self.data_job_key.job_id,
            custom_properties=custom_properties,
        )

class DataHubRunTimeLineage:
    """Push DataProcessInstance lineage inputs/outputs and run events."""

    def __init__(self, *, client_config: DataHubLineageRuntimeConfig) -> None:
        self.client = DataHubClient(bootstrap_settings=client_config.bootstrap_settings)
        self.static_lineage = DataHubStaticLineage(client=self.client, data_job_key=client_config.data_job_key)
        self.stage_config = self.static_lineage.stage_config
        self.env = self.client.env
        self.inputs: list[str] = []
        self.outputs: list[str] = []
        self._active_context: ActiveRunContext | None = None
        self._dpi_builder = DataProcessInstanceMcpBuilder()

    @property
    def flow_urn(self) -> str:
        return self.static_lineage.flow_urn

    @property
    def job_urn(self) -> str:
        return self.static_lineage.job_urn

    def dataset_urn(self, *, platform: str, name: str, env: str | None = None) -> DatasetUrn:
        return self.client.dataset_urn(platform=platform, name=name, env=env)

    def gql_scroll(self, urn: str, direction: str, count: int = 200) -> list[str]:
        return self.client.gql_scroll(urn, direction, count)

    def reset_io(self) -> None:
        self.inputs.clear()
        self.outputs.clear()

    def start_run(
        self,
        *,
        attempt: int = 1,
        datajob_urn: str | None = None,
        external_url: str | None = None,
        actor_urn: str = DEFAULT_ACTOR_URN,
    ) -> RunSpec:
        if self._active_context is not None:
            raise ValueError("A run is already active; call complete_run() before start_run().")
        self.reset_io()
        run = self.create_run_spec(job_version=self.resolve_job_version(), attempt=attempt)
        active_datajob_urn = datajob_urn or self.job_urn
        self._emit_run_status(
            datajob_urn=active_datajob_urn,
            run=run,
            status=DataProcessRunStatusClass.STARTED,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        self._active_context = ActiveRunContext(
            run=run,
            datajob_urn=active_datajob_urn,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        return run

    def add_input(self, *, name: str, platform: str, env: str | None = None) -> DatasetUrn:
        dataset = self.dataset_urn(platform=platform, name=name, env=env)
        self.inputs.append(str(dataset))
        return dataset

    def add_output(self, *, name: str, platform: str, env: str | None = None) -> DatasetUrn:
        dataset = self.dataset_urn(platform=platform, name=name, env=env)
        self.outputs.append(str(dataset))
        return dataset

    def build_run_spec(self, *, run_id: str, attempt: int, job_version: str) -> RunSpec:
        return RunSpec(
            run_id=run_id,
            attempt=attempt,
            job_version=job_version,
            inputs=list(self.inputs),
            outputs=list(self.outputs),
        )

    def create_run_spec(self, *, job_version: str, attempt: int = 1) -> RunSpec:
        run_id = f"{int(time.time() * 1000)}-{self.stage_config.job_name}-{uuid.uuid4()}"
        return self.build_run_spec(run_id=run_id, attempt=attempt, job_version=job_version)

    def emit_dpi(
        self,
        *,
        datajob_urn: str,
        run: RunSpec,
        external_url: str | None = None,
        actor_urn: str = DEFAULT_ACTOR_URN,
    ) -> str:
        self._emit_run_status(
            datajob_urn=datajob_urn,
            run=run,
            status=DataProcessRunStatusClass.STARTED,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        self._emit_run_status(
            datajob_urn=datajob_urn,
            run=run,
            status=DataProcessRunStatusClass.COMPLETE,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        return self._dpi_urn(run.run_id)

    def complete_run(self) -> str:
        if self._active_context is None:
            raise ValueError("No active run; call start_run() before complete_run().")
        context = self._active_context
        run = context.run
        completed_run = self.build_run_spec(
            run_id=run.run_id,
            attempt=run.attempt,
            job_version=run.job_version,
        )
        self._emit_run_status(
            datajob_urn=context.datajob_urn,
            run=completed_run,
            status=DataProcessRunStatusClass.COMPLETE,
            external_url=context.external_url,
            actor_urn=context.actor_urn,
        )
        self._clear_active_run()
        return self._dpi_urn(completed_run.run_id)

    def fail_run(self, error_message: str | None = None) -> str:
        _ = error_message
        if self._active_context is None:
            raise ValueError("No active run; call start_run() before fail_run().")
        context = self._active_context
        run = context.run
        failed_run = self.build_run_spec(
            run_id=run.run_id,
            attempt=run.attempt,
            job_version=run.job_version,
        )
        self._emit_run_status(
            datajob_urn=context.datajob_urn,
            run=failed_run,
            status=DataProcessRunStatusClass.FAILURE,
            external_url=context.external_url,
            actor_urn=context.actor_urn,
        )
        self._clear_active_run()
        return self._dpi_urn(failed_run.run_id)

    def abort_run(self) -> None:
        self._clear_active_run()

    def resolve_job_version(self) -> str:
        if value := os.getenv("DATAHUB_JOB_VERSION"):
            return value
        if value := os.getenv("GIT_SHA"):
            return f"git:{value}"
        if value := os.getenv("APP_VERSION"):
            return f"app:{value}"
        if value := os.getenv("IMAGE_DIGEST"):
            return f"image:{value}"
        if value := os.getenv("IMAGE_TAG"):
            return f"image:{value}"
        if value := self._local_git_sha():
            return f"git:{value}"
        return "unknown"

    def emit_dpi_event(
        self,
        *,
        datajob_urn: str,
        run: RunSpec,
        status: DataProcessRunStatusClass,
        external_url: str | None = None,
        actor_urn: str = DEFAULT_ACTOR_URN,
    ) -> str:
        dpi_urn = self._dpi_urn(run.run_id)
        mcps = self._dpi_builder.build(
            dpi_urn=dpi_urn,
            datajob_urn=datajob_urn,
            run=run,
            now_ms=self._now_ms(),
            status=status,
            actor_urn=actor_urn,
            external_url=external_url,
        )
        self.client.emit_mcps(mcps=mcps)
        return dpi_urn

    def _emit_run_status(
        self,
        *,
        datajob_urn: str,
        run: RunSpec,
        status: DataProcessRunStatusClass,
        external_url: str | None,
        actor_urn: str,
    ) -> str:
        return self.emit_dpi_event(
            datajob_urn=datajob_urn,
            run=run,
            status=status,
            external_url=external_url,
            actor_urn=actor_urn,
        )

    def _dpi_urn(self, run_id: str) -> str:
        return DataHubUrnFactory.data_process_instance_urn(run_id=run_id)

    def _now_ms(self) -> int:
        return int(time.time() * 1000)

    def _local_git_sha(self) -> str | None:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        value = result.stdout.strip()
        return value or None

    def _clear_active_run(self) -> None:
        self._active_context = None


class DataHubLineageClient(DataHubRunTimeLineage):
    """Backward-compatible alias for DataHubRunTimeLineage."""
