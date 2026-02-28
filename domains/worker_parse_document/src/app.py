"""worker_parse_document entrypoint.

Purpose:
- Bootstrap the parse stage worker that transforms raw objects into processed payloads.

What this module should do:
- Load queue/storage runtime settings.
- Wire parser registry and storage/queue clients.
- Construct the parse service and start the long-running loop.

Best practices:
- Keep only dependency wiring in this module.
- Register parsers explicitly so supported formats are easy to audit.
- Keep startup deterministic and free of hidden global side effects.
"""

from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from services.worker_parse_document_service import WorkerParseDocumentService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_parse_document"),
    )
    lineage = runtime_factory.runtime_context.lineage_gateway
    raw_config = runtime_factory.runtime_context.job_properties
    job_config, queue_config = _extract_job_and_queue_config(raw_config)

    stage_queue = runtime_factory.runtime_context.stage_queue_gateway
    parser_registry = ParserRegistry(parsers=[HtmlParser()])
    object_storage = runtime_factory.runtime_context.object_storage_gateway
    WorkerParseDocumentService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(job_config["poll_interval_seconds"]),
            "queue": queue_config,
            "storage": job_config["storage"],
            "security": job_config["security"],
        },
        parser_registry=parser_registry,
    ).serve()


def _extract_job_and_queue_config(expanded_config: dict) -> tuple[dict, dict]:
    """Return job and queue config sections from job properties."""
    job_config = expanded_config["job"]
    return job_config, job_config["queue"]


if __name__ == "__main__":
    run()
