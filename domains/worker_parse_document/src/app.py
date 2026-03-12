"""worker_parse_document entrypoint."""

from contracts.contracts import ParseWorkerConfigContract
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from registry import DataHubDataJobKey, DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from services.worker_parse_document_service import WorkerParseDocumentService
from startup.config_extractor import ParseConfigExtractor
from startup.service_factory import ParseServiceFactory


def run() -> None:
    """Start parse_document worker."""
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

    worker_config: ParseWorkerConfigContract = ParseConfigExtractor().extract(runtime_context.job_properties)
    service: WorkerParseDocumentService = ParseServiceFactory(
        parser_registry=ParserRegistry(parsers=[HtmlParser()]),
    ).build(runtime_context, worker_config)
    service.serve()


if __name__ == "__main__":
    run()
