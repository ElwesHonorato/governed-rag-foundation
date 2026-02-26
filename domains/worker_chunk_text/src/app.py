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
    InfrastructureFactory,
    RuntimeContextFactory,
)
from services.worker_chunk_text_service import WorkerChunkTextService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_chunk_text"),
    )
    runtime = runtime_factory.runtime_context
    infra = InfrastructureFactory(runtime)
    lineage = infra.datahub_lineage_client
    raw_config = infra.job_properties
    job_config, queue_config = _extract_job_and_queue_config(raw_config)

    stage_queue = infra.stage_queue
    object_storage = infra.object_storage
    WorkerChunkTextService(
        stage_queue=stage_queue,
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(job_config["poll_interval_seconds"]),
            "queue": queue_config,
            "storage": job_config["storage"],
        },
    ).serve()


def _extract_job_and_queue_config(expanded_config: dict) -> tuple[dict, dict]:
    """Return job and queue config sections from job properties."""
    job_config = expanded_config["job"]
    return job_config, job_config["queue"]


if __name__ == "__main__":
    run()
