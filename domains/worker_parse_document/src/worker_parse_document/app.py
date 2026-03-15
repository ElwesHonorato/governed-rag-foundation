"""Installable entrypoint for the ``worker_parse_document`` domain."""

from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_parse_document.services.worker_parse_document_service import WorkerParseDocumentService
from worker_parse_document.startup.config_extractor import ParseConfigExtractor
from worker_parse_document.startup.contracts import RuntimeParseJobConfig
from worker_parse_document.startup.service_factory import ParseServiceFactory


def run() -> None:
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_PARSE_DOCUMENT
    )
    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=data_job_key,
        settings_bundle=settings,
    ).build()
    runtime_job_config: RuntimeParseJobConfig = ParseConfigExtractor().extract(
        runtime_context.job_properties,
        env=runtime_context.env,
    )
    service: WorkerParseDocumentService = ParseServiceFactory().build(runtime_context, runtime_job_config)
    service.serve()


def main() -> int:
    run()
    return 0
