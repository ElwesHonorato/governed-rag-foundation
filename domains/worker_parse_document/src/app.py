"""worker_parse_document entrypoint."""

from contracts.contracts import ParseWorkerConfigContract
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from registry import DataHubPipelineJobs
from pipeline_common.settings import SettingsProvider, SettingsRequest
from pipeline_common.startup import RuntimeContextFactory, WorkerRuntimeLauncher
from services.worker_parse_document_service import WorkerParseDocumentService
from startup.config_extractor import ParseConfigExtractor
from startup.service_factory import ParseServiceFactory


def run() -> None:
    """Start parse_document worker."""
    settings = SettingsProvider(SettingsRequest(datahub=True, storage=True, queue=True)).bundle
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_parse_document"),
        settings_bundle=settings,
    )
    WorkerRuntimeLauncher[ParseWorkerConfigContract, WorkerParseDocumentService](
        runtime_factory=runtime_factory,
        config_extractor=ParseConfigExtractor(),
        service_factory=ParseServiceFactory(parser_registry=ParserRegistry(parsers=[HtmlParser()])),
    ).start()


if __name__ == "__main__":
    run()
