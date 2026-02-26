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
    build_datahub_lineage_client,
    build_object_storage,
    build_stage_queue,
    expand_dot_properties,
    load_runtime_settings,
)
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from services.worker_parse_document_service import WorkerParseDocumentService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, datahub_settings = load_runtime_settings()
    lineage = build_datahub_lineage_client(
        datahub_settings=datahub_settings,
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_parse_document"),
    )
    raw_config = expand_dot_properties(lineage.resolved_job_config.custom_properties)
    parse_config, queue_config = _extract_parse_and_queue_config(raw_config)

    stage_queue = build_stage_queue(
        broker_url=queue_settings.broker_url,
        queue_config=queue_config,
    )
    parser_registry = ParserRegistry(parsers=[HtmlParser()])
    object_storage = build_object_storage(s3_settings)
    WorkerParseDocumentService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(parse_config["poll_interval_seconds"]),
            "queue": queue_config,
            "storage": parse_config["storage"],
            "security": parse_config["security"],
        },
        parser_registry=parser_registry,
    ).serve()


def _extract_parse_and_queue_config(expanded_config: dict) -> tuple[dict, dict]:
    """Return parse and queue config sections from expanded properties."""
    return expanded_config["parse"], expanded_config["queue"]


if __name__ == "__main__":
    run()
