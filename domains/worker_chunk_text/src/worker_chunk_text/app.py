"""Installable entrypoint for the ``worker_chunk_text`` domain."""

from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_chunk_text.service.worker_chunking_service import WorkerChunkingService
from worker_chunk_text.startup.config_extractor import ChunkTextConfigExtractor
from worker_chunk_text.startup.contracts import RuntimeChunkJobConfig
from worker_chunk_text.startup.service_factory import ChunkTextServiceFactory


def main() -> int:
    worker_chunk_text_settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    worker_chunk_text_data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_CHUNK_TEXT
    )
    worker_chunk_text_runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=worker_chunk_text_data_job_key,
        settings_bundle=worker_chunk_text_settings,
    ).build()
    worker_chunk_text_runtime_job_config: RuntimeChunkJobConfig = ChunkTextConfigExtractor().extract(
        worker_chunk_text_runtime_context.job_properties,
        env=worker_chunk_text_runtime_context.env,
    )
    worker_chunk_text_service: WorkerChunkingService = ChunkTextServiceFactory().build(
        worker_chunk_text_runtime_context,
        worker_chunk_text_runtime_job_config,
    )
    worker_chunk_text_service.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
