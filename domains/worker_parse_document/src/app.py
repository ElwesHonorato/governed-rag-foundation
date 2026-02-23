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

from pipeline_common.queue import StageQueue
from pipeline_common.startup import (
    build_lineage_emitter,
    build_object_storage,
    load_worker_runtime_settings,
)
from configs.constants import PARSE_DOCUMENT_LINEAGE_CONFIG, PARSE_DOCUMENT_PROCESSING_CONFIG
from parsing.html import HtmlParser
from parsing.registry import ParserRegistry
from services.worker_parse_document_service import WorkerParseDocumentService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, lineage_settings = load_worker_runtime_settings()
    processing_config = PARSE_DOCUMENT_PROCESSING_CONFIG
    lineage = build_lineage_emitter(
        lineage_settings=lineage_settings,
        lineage_config=PARSE_DOCUMENT_LINEAGE_CONFIG,
    )
    stage_queue = StageQueue(queue_settings.broker_url, queue_config=processing_config["queue"])
    parser_registry = ParserRegistry(parsers=[HtmlParser()])
    object_storage = build_object_storage(s3_settings)
    WorkerParseDocumentService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config=processing_config,
        parser_registry=parser_registry,
    ).serve()


if __name__ == "__main__":
    run()
