import time
import json
import uuid
import os
import subprocess

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
from datahub.sdk import DataHubClient, DataFlow, DataJob, Dataset

from pipeline_common.lineage.contracts import DataHubDataJobKey, ResolvedDataHubFlowConfig

from .contracts import DataHubLineageRuntimeConfig, RunSpec


class DataHubLineageClient:
    """Reusable DataHub lineage client based on the validated DPI test model."""

    def __init__(
        self,
        *,
        client_config: DataHubLineageRuntimeConfig,
    ) -> None:
        """Initialize DataHub client wrapper for lineage operations."""
        bootstrap_settings = client_config.bootstrap_settings
        self.server = str(bootstrap_settings["server"])
        self.env = str(bootstrap_settings["env"])
        token_value = bootstrap_settings.get("token")
        self.token = str(token_value) if token_value else None
        self.client = DataHubClient(server=self.server, token=self.token)
        graph_timeout_sec = float(os.getenv("DATAHUB_TIMEOUT_SEC", "3"))
        self.graph = DataHubGraph(
            DatahubClientConfig(
                server=self.server,
                token=self.token,
                timeout_sec=graph_timeout_sec,
                retry_max_times=1,
            )
        )
        self.input_flow_urn = self._build_flow_urn_from_key(client_config.data_job_key)
        self.input_job_urn = self._build_job_urn_from_key(client_config.data_job_key)
        self.stage_config = self._resolve_stage_config(data_job_key=client_config.data_job_key)
        self.inputs: list[str] = []
        self.outputs: list[str] = []
        self._active_run: RunSpec | None = None
        self._active_datajob_urn: str | None = None
        self._active_external_url: str | None = None
        self._active_actor_urn: str = "urn:li:corpuser:datahub"

    def gql_scroll(self, graphql_endpoint: str, urn: str, direction: str, count: int = 200) -> list[str]:
        """Query lineage traversal for one entity and return connected URNs."""
        query = self._build_scroll_query(urn=urn, direction=direction, count=count)
        payload = self._graphql(graphql_endpoint=graphql_endpoint, query=query)
        return self._extract_scroll_urns(payload)

    def upsert_datasets(self, dataset_urns: list[str], description: str | None = None) -> None:
        """Upsert dataset entities so run and lineage writes have valid targets."""
        dataset_description = description or "dataset created by DataHubLineageClient"
        for urn_str in dataset_urns:
            self._upsert_dataset(urn_str=urn_str, description=dataset_description)

    def dataset_urn(self, *, platform: str, name: str, env: str | None = None) -> DatasetUrn:
        """Build a DatasetUrn using explicit platform/name and default client env."""
        return DatasetUrn(
            platform=platform,
            name=name,
            env=env or self.env,
        )

    def reset_io(self) -> None:
        """Clear in-memory inputs and outputs for the next run."""
        self.inputs.clear()
        self.outputs.clear()

    def start_run(
        self,
        *,
        attempt: int = 1,
        datajob_urn: str | None = None,
        external_url: str | None = None,
        actor_urn: str = "urn:li:corpuser:datahub",
    ) -> RunSpec:
        """Start one run by resetting IO, creating run metadata, and emitting STARTED."""
        if self._active_run is not None:
            raise ValueError("A run is already active; call complete_run() before start_run().")
        self.reset_io()
        run = self.create_run_spec(job_version=self.resolve_job_version(), attempt=attempt)
        self.emit_dpi_event(
            datajob_urn=datajob_urn or self.job_urn,
            run=run,
            status=DataProcessRunStatusClass.STARTED,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        self._active_run = run
        self._active_datajob_urn = datajob_urn or self.job_urn
        self._active_external_url = external_url
        self._active_actor_urn = actor_urn
        return run

    def add_input(self, *, name: str, platform: str, env: str | None = None) -> DatasetUrn:
        """Build one input DatasetUrn and append it to current in-memory run state."""
        dataset = self.dataset_urn(platform=platform, name=name, env=env)
        self.inputs.append(str(dataset))
        return dataset

    def add_output(self, *, name: str, platform: str, env: str | None = None) -> DatasetUrn:
        """Build one output DatasetUrn and append it to current in-memory run state."""
        dataset = self.dataset_urn(platform=platform, name=name, env=env)
        self.outputs.append(str(dataset))
        return dataset

    def build_run_spec(self, *, run_id: str, attempt: int, job_version: str) -> RunSpec:
        """Build RunSpec from current in-memory inputs/outputs."""
        return RunSpec(
            run_id=run_id,
            attempt=attempt,
            job_version=job_version,
            inputs=list(self.inputs),
            outputs=list(self.outputs),
        )

    def create_run_spec(self, *, job_version: str, attempt: int = 1) -> RunSpec:
        """Build RunSpec from current IO state with an auto-generated run id."""
        run_id = f"{int(time.time() * 1000)}-{self.stage_config.job_name}-{uuid.uuid4()}"
        return self.build_run_spec(run_id=run_id, attempt=attempt, job_version=job_version)

    def upsert_flow_and_job(
        self,
        *,
        flow_platform: str,
        flow_name: str,
        flow_instance: str,
        job_name: str,
        flow_description: str = "pipeline for run-level lineage testing",
        job_description: str = "job for run-level lineage testing",
    ) -> tuple[DataFlow, DataJob]:
        """Upsert one DataFlow and one DataJob template entity."""
        flow = self._build_flow(
            flow_platform=flow_platform,
            flow_name=flow_name,
            flow_instance=flow_instance,
            flow_description=flow_description,
        )
        self.client.entities.upsert(flow)
        job = self._build_job(job_name=job_name, flow=flow, job_description=job_description)
        self.client.entities.upsert(job)
        return flow, job

    def upsert_stage_flow_and_job(
        self,
        *,
        flow_description: str = "pipeline for run-level lineage testing",
        job_description: str = "job for run-level lineage testing",
    ) -> tuple[DataFlow, DataJob]:
        """Upsert DataFlow/DataJob using this client's resolved runtime config."""
        return self.upsert_flow_and_job(
            flow_platform=self.stage_config.flow_platform,
            flow_name=self.stage_config.flow_name,
            flow_instance=self.env,
            job_name=self.stage_config.job_name,
            flow_description=flow_description,
            job_description=job_description,
        )

    @property
    def flow_urn(self) -> str:
        """Build deterministic DataFlow URN for this client stage."""
        return self.stage_config.flow_urn(self.env)

    @property
    def job_urn(self) -> str:
        """Build deterministic DataJob URN for this client stage."""
        return self.stage_config.job_urn(self.env)

    def emit_dpi(
        self,
        *,
        datajob_urn: str,
        run: RunSpec,
        external_url: str | None = None,
        actor_urn: str = "urn:li:corpuser:datahub",
    ) -> str:
        """Emit a DataProcessInstance with properties, relationships, IO, and run events."""
        self.emit_dpi_event(
            datajob_urn=datajob_urn,
            run=run,
            status=DataProcessRunStatusClass.STARTED,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        self.emit_dpi_event(
            datajob_urn=datajob_urn,
            run=run,
            status=DataProcessRunStatusClass.COMPLETE,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        return self._dpi_urn(run.run_id)

    def complete_run(self) -> str:
        """Complete one existing run id using the current IO state."""
        if self._active_run is None:
            raise ValueError("No active run; call start_run() before complete_run().")
        run = self._active_run
        completed_run = self.build_run_spec(
            run_id=run.run_id,
            attempt=run.attempt,
            job_version=run.job_version,
        )
        self.upsert_datasets(completed_run.inputs + completed_run.outputs)
        self.emit_dpi_event(
            datajob_urn=self._active_datajob_urn or self.job_urn,
            run=completed_run,
            status=DataProcessRunStatusClass.COMPLETE,
            external_url=self._active_external_url,
            actor_urn=self._active_actor_urn,
        )
        self._active_run = None
        self._active_datajob_urn = None
        self._active_external_url = None
        self._active_actor_urn = "urn:li:corpuser:datahub"
        return self._dpi_urn(completed_run.run_id)

    def resolve_job_version(self) -> str:
        """Resolve job version from runtime metadata with sensible fallbacks."""
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
        actor_urn: str = "urn:li:corpuser:datahub",
    ) -> str:
        """Emit one DataProcessInstance run event with associated run metadata and IO."""
        dpi_urn = self._dpi_urn(run.run_id)
        now_ms = self._now_ms()
        props = self._build_dpi_properties(run=run, now_ms=now_ms, actor_urn=actor_urn, external_url=external_url)
        rel = self._build_dpi_relationships(datajob_urn=datajob_urn)
        dpi_in, dpi_out = self._build_dpi_io(run=run)
        run_event = self._build_run_event(run=run, now_ms=now_ms, status=status)
        mcps = self._build_dpi_mcps(
            dpi_urn=dpi_urn,
            properties=props,
            relationships=rel,
            dpi_input=dpi_in,
            dpi_output=dpi_out,
            run_event=run_event,
        )
        self._emit_mcps(mcps=mcps)
        return dpi_urn

    def _build_scroll_query(self, urn: str, direction: str, count: int) -> str:
        """Build one GraphQL scrollAcrossLineage query."""
        urn_literal = json.dumps(urn)
        return (
            "query {"
            " scrollAcrossLineage(input: {"
            f" urn: {urn_literal}, direction: {direction}, count: {count}"
            " }) {"
            " searchResults { entity { urn type } }"
            " }"
            "}"
        )

    def _graphql(self, graphql_endpoint: str, query: str) -> dict:
        """Execute one GraphQL query and return JSON payload."""
        response = requests.post(graphql_endpoint, json={"query": query}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(payload["errors"])
        return payload

    def _extract_scroll_urns(self, payload: dict) -> list[str]:
        """Extract URNs from one scrollAcrossLineage GraphQL payload."""
        results = payload.get("data", {}).get("scrollAcrossLineage", {}).get("searchResults", [])
        return [item.get("entity", {}).get("urn", "") for item in results]

    def _upsert_dataset(self, urn_str: str, description: str) -> None:
        """Upsert one dataset entity by URN."""
        urn = DatasetUrn.from_string(urn_str)
        self.client.entities.upsert(
            Dataset(
                platform=urn.platform,
                name=urn.name,
                env=urn.env,
                description=description,
            )
        )

    def _resolve_stage_config(
        self,
        *,
        data_job_key: DataHubDataJobKey,
    ) -> ResolvedDataHubFlowConfig:
        """Resolve flow/job config using deterministic naming and DataHub custom properties."""
        job_info = self._get_datajob_info(self.input_job_urn)
        custom_properties = {}
        if job_info is not None and isinstance(job_info.customProperties, dict):
            custom_properties = {str(k): str(v) for k, v in job_info.customProperties.items()}
        return ResolvedDataHubFlowConfig(
            flow_id=data_job_key.flow_id,
            job_id=data_job_key.job_id,
            flow_platform=data_job_key.flow_platform,
            flow_name=data_job_key.flow_id,
            flow_instance=self.env,
            job_name=data_job_key.job_id,
            custom_properties=custom_properties,
        )

    def _build_flow_urn_from_key(self, data_job_key: DataHubDataJobKey) -> str:
        """Build deterministic DataFlow URN from input key and runtime env."""
        return (
            f"urn:li:dataFlow:({data_job_key.flow_platform},"
            f"{self.env}.{data_job_key.flow_id},{self.env})"
        )

    def _build_job_urn_from_key(self, data_job_key: DataHubDataJobKey) -> str:
        """Build deterministic DataJob URN from input key and runtime env."""
        return f"urn:li:dataJob:({self._build_flow_urn_from_key(data_job_key)},{data_job_key.job_id})"

    def _get_datajob_info(self, job_urn: str) -> DataJobInfoClass | None:
        """Read DataJobInfo aspect for one job URN from DataHub."""

        try:
            with self.graph:
                return self.graph.get_aspect(job_urn, DataJobInfoClass)
        except Exception:
            return None

    def _build_flow(
        self,
        *,
        flow_platform: str,
        flow_name: str,
        flow_instance: str,
        flow_description: str,
    ) -> DataFlow:
        """Build one DataFlow entity payload."""
        return DataFlow(
            platform=flow_platform,
            name=flow_name,
            platform_instance=flow_instance,
            description=flow_description,
        )

    def _build_job(self, *, job_name: str, flow: DataFlow, job_description: str) -> DataJob:
        """Build one DataJob entity payload."""
        return DataJob(name=job_name, flow=flow, description=job_description)

    def _dpi_urn(self, run_id: str) -> str:
        """Build DataProcessInstance URN for one run id."""
        return f"urn:li:dataProcessInstance:{run_id}"

    def _now_ms(self) -> int:
        """Return current epoch time in milliseconds."""
        return int(time.time() * 1000)

    def _local_git_sha(self) -> str | None:
        """Return local git short SHA when available."""
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

    def _build_dpi_properties(
        self,
        *,
        run: RunSpec,
        now_ms: int,
        actor_urn: str,
        external_url: str | None,
    ) -> DataProcessInstancePropertiesClass:
        """Build DataProcessInstance properties aspect."""
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

    def _build_dpi_relationships(self, *, datajob_urn: str) -> DataProcessInstanceRelationshipsClass:
        """Build DataProcessInstance relationships aspect."""
        return DataProcessInstanceRelationshipsClass(upstreamInstances=[], parentTemplate=datajob_urn)

    def _build_dpi_io(self, *, run: RunSpec) -> tuple[DataProcessInstanceInput, DataProcessInstanceOutput]:
        """Build DataProcessInstance input and output aspects."""
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
        """Build one run event aspect for a specific status."""
        return DataProcessInstanceRunEventClass(
            timestampMillis=now_ms,
            status=status,
            attempt=run.attempt,
        )

    def _build_dpi_mcps(
        self,
        *,
        dpi_urn: str,
        properties: DataProcessInstancePropertiesClass,
        relationships: DataProcessInstanceRelationshipsClass,
        dpi_input: DataProcessInstanceInput,
        dpi_output: DataProcessInstanceOutput,
        run_event: DataProcessInstanceRunEventClass,
    ) -> list[MetadataChangeProposalWrapper]:
        """Build ordered MCP list for one DataProcessInstance event emission."""
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

    def _emit_mcps(self, *, mcps: list[MetadataChangeProposalWrapper]) -> None:
        """Emit MCPs to DataHub graph client in order."""
        with self.graph:
            for mcp in mcps:
                self.graph.emit(mcp)
