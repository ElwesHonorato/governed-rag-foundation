"""Runtime DataHub job key registry.

This module is intentionally limited to runtime bootstrap identifiers
(flow_id/job_id/platform) so workers can resolve their DataHub job key
without a runtime dependency on the governance repository.

Ownership note:
- Governance remains the source of truth for static topology mutations.
- Runtime lineage must not mutate static DataHub entities.
"""

from enum import Enum

from pipeline_common.lineage.contracts import DataHubDataJobKey


class DataHubPipelineJobs(Enum):
    """Pipeline job references extracted from governance definitions."""

    CUSTOM_GOVERNED_RAG = {
        "worker_scan": DataHubDataJobKey("governed-rag", "worker_scan", "custom"),
        "worker_parse_document": DataHubDataJobKey("governed-rag", "worker_parse_document", "custom"),
        "worker_chunk_text": DataHubDataJobKey("governed-rag", "worker_chunk_text", "custom"),
        "worker_embed_chunks": DataHubDataJobKey("governed-rag", "worker_embed_chunks", "custom"),
        "worker_index_weaviate": DataHubDataJobKey("governed-rag", "worker_index_weaviate", "custom"),
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
    def job_ids(self) -> tuple[str, ...]:
        return tuple(self.value.keys())

    def job(self, job_id: str) -> DataHubDataJobKey:
        if job_id not in self.value:
            raise ValueError(f"Unknown job_id '{job_id}' for pipeline '{self.name}'.")
        return self.value[job_id]

__all__ = ["DataHubPipelineJobs", "DataHubDataJobKey"]
