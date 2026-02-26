"""worker_chunk_text entrypoint.

Purpose:
- Bootstrap the chunking worker that converts processed documents into chunk artifacts.

What this module should do:
- Read queue and storage settings from environment.
- Create queue/storage gateways.
- Construct the chunking service and run it.

Best practices:
- Keep this file focused on composition, not transformation logic.
- Keep worker configuration sourced from DataHub job `custom_properties`.
- Ensure queue contract and service wiring stay aligned when stages evolve.
"""

from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.startup import (
    build_datahub_lineage_client,
    build_object_storage,
    build_stage_queue,
    expand_dot_properties,
    load_runtime_settings,
)
from services.worker_chunk_text_service import WorkerChunkTextService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, datahub_settings = load_runtime_settings()
    lineage = build_datahub_lineage_client(
        datahub_settings=datahub_settings,
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_chunk_text"),
    )
    raw_config = expand_dot_properties(lineage.resolved_job_config.custom_properties)
    chunk_config, queue_config = _extract_chunk_and_queue_config(raw_config)

    stage_queue = build_stage_queue(
        broker_url=queue_settings.broker_url,
        queue_config=queue_config,
    )
    object_storage = build_object_storage(s3_settings)
    WorkerChunkTextService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(chunk_config["poll_interval_seconds"]),
            "queue": queue_config,
            "storage": chunk_config["storage"],
        },
    ).serve()


def _extract_chunk_and_queue_config(expanded_config: dict) -> tuple[dict, dict]:
    """Return chunk and queue config sections from expanded properties."""
    return expanded_config["chunk"], expanded_config["queue"]


if __name__ == "__main__":
    run()
