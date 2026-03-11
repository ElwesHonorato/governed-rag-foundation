"""worker_parse_document entrypoint."""

from contracts.contracts import ParseWorkerConfigContract
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from registry import DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_parse_document_service import WorkerParseDocumentService
from startup.config_extractor import ParseConfigExtractor
from startup.service_factory import ParseServiceFactory


def run() -> None:
    """Start parse_document worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True, spark=False)).bundle
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(GovernedRagJobId.WORKER_PARSE_DOCUMENT),
        settings_bundle=settings,
    )
    WorkerRuntimeLauncher[ParseWorkerConfigContract, WorkerParseDocumentService](
        runtime_context=runtime_factory.build_runtime_context(),
        config_extractor=ParseConfigExtractor(),
        service_factory=ParseServiceFactory(parser_registry=ParserRegistry(parsers=[HtmlParser()])),
    ).start()


if __name__ == "__main__":
    run()
