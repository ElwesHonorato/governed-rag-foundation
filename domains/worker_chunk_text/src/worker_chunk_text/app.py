"""Installable entrypoint for the ``worker_chunk_text`` domain."""

from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_chunk_text.service.worker_chunking_service import WorkerChunkingService
from worker_chunk_text.startup.config_extractor import ChunkTextConfigExtractor
from worker_chunk_text.startup.contracts import RuntimeChunkJobConfig
from worker_chunk_text.startup.service_factory import ChunkTextServiceFactory


def run() -> None:
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_CHUNK_TEXT
    )
    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=data_job_key,
        settings_bundle=settings,
    ).build()
    runtime_job_config: RuntimeChunkJobConfig = ChunkTextConfigExtractor().extract(
        runtime_context.job_properties,
        env=runtime_context.env,
    )
    service: WorkerChunkingService = ChunkTextServiceFactory().build(runtime_context, runtime_job_config)
    service.serve()


def main() -> int:
    run()
    return 0
