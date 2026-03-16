"""Installable entrypoint for the ``worker_parse_document`` domain."""

from pipeline_common.registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from worker_parse_document.services.worker_parse_document_service import WorkerParseDocumentService
from worker_parse_document.startup.config_extractor import ParseConfigExtractor
from worker_parse_document.startup.contracts import RuntimeParseJobConfig
from worker_parse_document.startup.service_factory import ParseServiceFactory


def main() -> int:
    worker_parse_document_settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle
    worker_parse_document_data_job_key: DataHubDataJobKey = DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(
        GovernedRagJobId.WORKER_PARSE_DOCUMENT
    )
    worker_parse_document_runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=worker_parse_document_data_job_key,
        settings_bundle=worker_parse_document_settings,
    ).build()
    worker_parse_document_runtime_job_config: RuntimeParseJobConfig = ParseConfigExtractor().extract(
        worker_parse_document_runtime_context.job_properties,
        env=worker_parse_document_runtime_context.env,
    )
    worker_parse_document_service: WorkerParseDocumentService = ParseServiceFactory().build(
        worker_parse_document_runtime_context,
        worker_parse_document_runtime_job_config,
    )
    worker_parse_document_service.serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
