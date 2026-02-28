"""worker_manifest entrypoint.

Purpose:
- Bootstrap the manifest worker that materializes per-document stage status metadata.

What this module should do:
- Load storage settings.
- Build object storage gateway.
- Construct the manifest service and start the polling loop.

Best practices:
- Keep this file minimal and orchestration-focused.
- Avoid embedding stage status rules here; keep those in service logic.
- Keep startup dependencies explicit so runtime behavior is predictable.
"""

from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.settings import DataHubSettings, QueueRuntimeSettings, S3StorageSettings
from pipeline_common.startup import (
    RuntimeContextFactory,
)
from services.worker_manifest_service import WorkerManifestService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    runtime_factory = RuntimeContextFactory(
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_manifest"),
        datahub_settings=DataHubSettings.from_env(),
        s3_settings=S3StorageSettings.from_env(),
        queue_settings=QueueRuntimeSettings.from_env(),
    )
    lineage = runtime_factory.runtime_context.lineage_gateway
    raw_config = runtime_factory.runtime_context.job_properties
    job_config = _extract_job_config(raw_config)

    object_storage = runtime_factory.runtime_context.object_storage_gateway
    WorkerManifestService(
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(job_config["poll_interval_seconds"]),
            "storage": job_config["storage"],
        },
    ).serve()


def _extract_job_config(expanded_config: dict) -> dict:
    """Return job config section from job properties."""
    return expanded_config["job"]


if __name__ == "__main__":
    run()
