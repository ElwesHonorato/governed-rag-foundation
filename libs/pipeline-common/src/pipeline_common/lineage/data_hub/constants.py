from enum import Enum

from pipeline_common.config import JobStageName

from pipeline_common.lineage.contracts import DataHubFlowConfig


class DataHubStageFlowConfig(Enum):
    """DataHub flow/job configuration by worker stage."""

    WORKER_SCAN = DataHubFlowConfig(
        flow_platform="custom",
        flow_name="governed-rag",
        flow_instance="PROD",
        job_name=JobStageName.WORKER_SCAN.value,
    )
    WORKER_PARSE_DOCUMENT = DataHubFlowConfig(
        flow_platform="custom",
        flow_name="governed-rag",
        flow_instance="PROD",
        job_name=JobStageName.WORKER_PARSE_DOCUMENT.value,
    )
    WORKER_CHUNK_TEXT = DataHubFlowConfig(
        flow_platform="custom",
        flow_name="governed-rag",
        flow_instance="PROD",
        job_name=JobStageName.WORKER_CHUNK_TEXT.value,
    )
    WORKER_EMBED_CHUNKS = DataHubFlowConfig(
        flow_platform="custom",
        flow_name="governed-rag",
        flow_instance="PROD",
        job_name=JobStageName.WORKER_EMBED_CHUNKS.value,
    )
    WORKER_INDEX_WEAVIATE = DataHubFlowConfig(
        flow_platform="custom",
        flow_name="governed-rag",
        flow_instance="PROD",
        job_name=JobStageName.WORKER_INDEX_WEAVIATE.value,
    )

    @property
    def flow_platform(self) -> str:
        return self.value.flow_platform

    @property
    def flow_name(self) -> str:
        return self.value.flow_name

    @property
    def flow_instance(self) -> str:
        return self.value.flow_instance

    @property
    def job_name(self) -> str:
        return self.value.job_name


__all__ = ["DataHubFlowConfig", "DataHubStageFlowConfig"]
