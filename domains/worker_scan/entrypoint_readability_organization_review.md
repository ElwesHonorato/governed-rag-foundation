# worker_scan Entrypoint Readability / Organization Review

## A) Short Critique (Current Readability Issues)
- `run()` currently mixes too many concerns inline (settings load, lineage build, config extraction, parsing, queue/storage wiring, service boot).
- Deep indexing and repeated path traversal (`processing_config["scan"][...]`, `processing_config["queue"][...]`) increases cognitive load.
- Helper naming is generic (`_build_processing_config`) and does not communicate source/intent (dot-notation expansion from DataHub properties).
- CSV extension parsing logic is embedded inside `run()` instead of being a tiny named helper.
- Variable naming is broad (`processing_config`) where narrower names (`scan_config`, `queue_config`) would improve scanability.
- Dependency creation order is correct, but the top-down orchestration story is harder to follow than it needs to be.
- Queue/storage object construction details distract from the orchestration flow.
- Some low-level helper details appear before the high-level run flow, reducing readability for first-time readers.
- Runtime assumptions (required keys) are implied by indexing, not expressed by small access helpers.

## B) Proposed “After” Structure
Top-level orchestration should read like this:
1. `run()`
2. `_load_runtime_settings()`
3. `_build_lineage_client(...)`
4. `_expand_dot_properties(...)`
5. `_extract_scan_and_queue_config(...)`
6. `_parse_extensions_csv(...)`
7. `_build_stage_queue(...)`
8. `_build_object_storage(...)`

Responsibilities:
- `run()` remains orchestration-only and top-down.
- Small helpers do one thing each and keep wiring details out of `run()`.
- Keep side effects explicit and early (`bootstrap_bucket_prefixes`) before service loop.

## C) Updated Code (Behavior Preserving, Readability Improved)
```python
"""worker_scan entrypoint.

Purpose:
- Bootstrap the scan stage worker that moves candidate files from incoming to raw storage.

What this module should do:
- Read runtime settings from environment.
- Build queue and object storage gateways.
- Initialize the scan processor and start the service loop.

Best practices:
- Keep orchestration-only code here; put business rules in services/processors.
- Fail fast on missing configuration and rely on typed config constants.
- Keep side effects explicit at startup (for example, bucket prefix bootstrap).
"""

from typing import Any

from pipeline_common.lineage.data_hub import DataHubLineageClient
from pipeline_common.lineage.data_hub.contracts import DataHubLineageRuntimeConfig
from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.queue import StageQueue
from pipeline_common.settings import (
    DataHubBootstrapSettings,
    QueueRuntimeSettings,
    S3StorageSettings,
)
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, datahub_settings = _load_runtime_settings()

    lineage_client = _build_lineage_client(datahub_settings)

    raw_config = _expand_dot_properties(lineage_client.stage_config.custom_properties)
    scan_config, queue_config = _extract_scan_and_queue_config(raw_config)

    extensions = _parse_extensions_csv(scan_config["filters"]["extensions"])

    stage_queue = _build_stage_queue(
        broker_url=queue_settings.broker_url,
        queue_config=queue_config,
    )
    object_storage = _build_object_storage(s3_settings)

    # Keep startup side effect explicit and early.
    object_storage.bootstrap_bucket_prefixes(scan_config["storage"]["bucket"])

    processor = StorageScanCycleProcessor(
        object_storage=object_storage,
        stage_queue=stage_queue,
        lineage=lineage_client,
        processing_config={
            "storage": scan_config["storage"],
            "filters": {"extensions": extensions},
        },
    )

    service = WorkerScanService(
        processor=processor,
        processing_config={"poll_interval_seconds": int(scan_config["poll_interval_seconds"])},
    )
    service.serve()


def _load_runtime_settings() -> tuple[S3StorageSettings, QueueRuntimeSettings, DataHubBootstrapSettings]:
    """Load environment-backed runtime settings."""
    return (
        S3StorageSettings.from_env(),
        QueueRuntimeSettings.from_env(),
        DataHubBootstrapSettings.from_env(),
    )


def _build_lineage_client(datahub_settings: DataHubBootstrapSettings) -> DataHubLineageClient:
    """Build DataHub lineage client for worker_scan."""
    return DataHubLineageClient(
        client_config=DataHubLineageRuntimeConfig(
            bootstrap_settings={
                "server": datahub_settings.server,
                "env": datahub_settings.env,
                "token": datahub_settings.token,
            },
            data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan"),
        )
    )


def _set_nested(target: dict[str, Any], dotted_key: str, value: str) -> None:
    """Set one dotted key (for example, 'scan.storage.bucket') into nested dict."""
    cursor: dict[str, Any] = target
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        cursor = cursor.setdefault(part, {})
    cursor[parts[-1]] = value


def _expand_dot_properties(custom_properties: dict[str, str]) -> dict[str, Any]:
    """Expand dot-notation custom properties into a nested mapping."""
    expanded: dict[str, Any] = {}
    for key, value in custom_properties.items():
        if "." in key:
            _set_nested(expanded, key, value)
    return expanded


def _extract_scan_and_queue_config(expanded_config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return scan and queue config sections from expanded properties."""
    return expanded_config["scan"], expanded_config["queue"]


def _parse_extensions_csv(value: Any) -> list[str]:
    """Parse comma-separated extension string into normalized list."""
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _build_stage_queue(*, broker_url: str, queue_config: dict[str, Any]) -> StageQueue:
    """Build queue gateway for worker scan stage."""
    return StageQueue(
        broker_url,
        queue_config=queue_config,
    )


def _build_object_storage(s3_settings: S3StorageSettings) -> ObjectStorageGateway:
    """Build object storage gateway from S3 settings."""
    return ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )


if __name__ == "__main__":
    run()
```

## D) Optional Micro-Pattern Upgrades (Minimal)
- Use local aliases immediately after config expansion:
  - `scan_config, queue_config = ...`
  - Why: removes repeated nested indexing and makes orchestration read as intent.
- Construct `service` as a local variable before `.serve()`:
  - Why: clearer lifecycle and easier to debug/trace startup wiring.
