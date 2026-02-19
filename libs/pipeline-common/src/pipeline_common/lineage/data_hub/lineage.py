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
    DataProcessInstancePropertiesClass,
    DataProcessInstanceRelationshipsClass,
    DataProcessInstanceRunEventClass,
    DataProcessRunStatusClass,
    EdgeClass,
)
from datahub.metadata.urns import DatasetUrn
from datahub.sdk import DataHubClient, DataFlow, DataJob, Dataset

from pipeline_common.lineage.data_hub.constants import DataHubStageFlowConfig
from pipeline_common.settings import DataHubBootstrapSettings

from .contracts import RunSpec


class DataHubLineageClient:
    """Reusable DataHub lineage client based on the validated DPI test model."""

    def __init__(
        self,
        stage: DataHubStageFlowConfig,
        settings: DataHubBootstrapSettings,
    ) -> None:
        """Initialize DataHub client wrapper for lineage operations."""
        self.server = settings.server
        self.stage = stage
        self.stage_config = stage.value
        self.token = settings.token
        self.env = settings.env
        self.client = DataHubClient(server=self.server, token=self.token)
        self.inputs: list[str] = []
        self.outputs: list[str] = []

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
        run_id = f"{int(time.time() * 1000)}-{self.stage.job_name}-{uuid.uuid4()}"
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
        """Upsert DataFlow/DataJob using this client's stage as the source of truth."""
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

    def push_run(
        self,
        *,
        attempt: int = 1,
        external_url: str | None = None,
        actor_urn: str = "urn:li:corpuser:datahub",
    ) -> str:
        """Create one run from current IO, upsert datasets, and emit START/COMPLETE events."""
        job_version = self.resolve_job_version()
        run = self.create_run_spec(job_version=job_version, attempt=attempt)
        self.upsert_datasets(run.inputs + run.outputs)
        self.emit_dpi_event(
            datajob_urn=self.job_urn,
            run=run,
            status=DataProcessRunStatusClass.STARTED,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        self.emit_dpi_event(
            datajob_urn=self.job_urn,
            run=run,
            status=DataProcessRunStatusClass.COMPLETE,
            external_url=external_url,
            actor_urn=actor_urn,
        )
        return self._dpi_urn(run.run_id)

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
        graph = DataHubGraph(DatahubClientConfig(server=self.server, token=self.token))
        with graph:
            for mcp in mcps:
                graph.emit(mcp)
