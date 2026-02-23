
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

from pipeline_common.startup import build_object_storage, load_storage_settings
from configs.constants import MANIFEST_PROCESSING_CONFIG
from services.worker_manifest_service import WorkerManifestService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings = load_storage_settings()
    processing_config = MANIFEST_PROCESSING_CONFIG
    object_storage = build_object_storage(s3_settings)
    WorkerManifestService(
        object_storage=object_storage,
        processing_config=processing_config,
    ).serve()


if __name__ == "__main__":
    run()
