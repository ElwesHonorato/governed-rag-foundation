"""Runtime DataHub job key registry.

This module is intentionally limited to runtime bootstrap identifiers
(flow_id/job_id/platform) so workers can resolve their DataHub job key
without a runtime dependency on the governance repository.

Ownership note:
- Governance remains the source of truth for static topology mutations.
- Runtime lineage must not mutate static DataHub entities.
"""

from enum import Enum

from pipeline_common.gateways.lineage.contracts import DataHubDataJobKey


class GovernedRagJobId(Enum):
    WORKER_SCAN = "worker_scan"
    WORKER_PARSE_DOCUMENT = "worker_parse_document"
    WORKER_CHUNK_TEXT = "worker_chunk_text"
    WORKER_EMBED_CHUNKS = "worker_embed_chunks"
    WORKER_INDEX_WEAVIATE = "worker_index_weaviate"
    WORKER_MANIFEST = "worker_manifest"
    WORKER_METRICS = "worker_metrics"


class DataHubPipelineJobs(Enum):
    """Pipeline job references extracted from governance definitions."""

    CUSTOM_GOVERNED_RAG = {
        GovernedRagJobId.WORKER_SCAN: DataHubDataJobKey("governed-rag", "worker_scan", "custom"),
        GovernedRagJobId.WORKER_PARSE_DOCUMENT: DataHubDataJobKey("governed-rag", "worker_parse_document", "custom"),
        GovernedRagJobId.WORKER_CHUNK_TEXT: DataHubDataJobKey("governed-rag", "worker_chunk_text", "custom"),
        GovernedRagJobId.WORKER_EMBED_CHUNKS: DataHubDataJobKey("governed-rag", "worker_embed_chunks", "custom"),
        GovernedRagJobId.WORKER_INDEX_WEAVIATE: DataHubDataJobKey("governed-rag", "worker_index_weaviate", "custom"),
        GovernedRagJobId.WORKER_MANIFEST: DataHubDataJobKey("governed-rag", "worker_manifest", "custom"),
        GovernedRagJobId.WORKER_METRICS: DataHubDataJobKey("governed-rag", "worker_metrics", "custom"),
    }

    @property
    def flow_platform(self) -> str:
        first_job = next(iter(self.value.values()))
        return first_job.flow_platform

    @property
    def flow_id(self) -> str:
        first_job = next(iter(self.value.values()))
        return first_job.flow_id

    @property
    def job_ids(self) -> tuple[GovernedRagJobId, ...]:
        return tuple(self.value.keys())

    def job(self, job_id: GovernedRagJobId) -> DataHubDataJobKey:
        if job_id not in self.value:
            raise ValueError(f"Unknown job_id '{job_id}' for pipeline '{self.name}'.")
        return self.value[job_id]

__all__ = ["DataHubPipelineJobs", "DataHubDataJobKey", "GovernedRagJobId"]
