"""worker_parse_document entrypoint."""

from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from registry import DataHubPipelineJobs, GovernedRagJobId
from pipeline_common.settings import SettingsBundle, SettingsProvider, SettingsRequest
from pipeline_common.startup import (
    RuntimeContextFactory,
    WorkerRuntimeLauncher,
)
from pipeline_common.startup.runtime_context import WorkerRuntimeContext
from startup.config_extractor import ParseConfigExtractor
from startup.service_factory import ParseServiceFactory


def run() -> None:
    """Start parse_document worker."""
    settings: SettingsBundle = SettingsProvider(
        SettingsRequest(datahub=True, storage=True, queue=True),
    ).bundle

    runtime_context: WorkerRuntimeContext = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job(GovernedRagJobId.WORKER_PARSE_DOCUMENT),
        settings_bundle=settings,
    ).build_runtime_context()

    WorkerRuntimeLauncher(
        runtime_context=runtime_context,
        config_extractor=ParseConfigExtractor(),
        service_factory=ParseServiceFactory(parser_registry=ParserRegistry(parsers=[HtmlParser()])),
    ).start()


if __name__ == "__main__":
    run()
