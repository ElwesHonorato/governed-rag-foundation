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
from pipeline_common.startup import (
    build_datahub_lineage_client,
    build_object_storage,
    expand_dot_properties,
    load_runtime_settings,
)
from services.worker_manifest_service import WorkerManifestService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, _, datahub_settings = load_runtime_settings()
    lineage = build_datahub_lineage_client(
        datahub_settings=datahub_settings,
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_manifest"),
    )
    raw_config = expand_dot_properties(lineage.resolved_job_config.custom_properties)
    manifest_config = raw_config["manifest"]

    object_storage = build_object_storage(s3_settings)
    WorkerManifestService(
        object_storage=object_storage,
        lineage=lineage,
        processing_config={
            "poll_interval_seconds": int(manifest_config["poll_interval_seconds"]),
            "storage": manifest_config["storage"],
        },
    ).serve()


if __name__ == "__main__":
    run()
