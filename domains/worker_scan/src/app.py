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

from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.startup import (
    build_datahub_lineage_client,
    build_object_storage,
    build_stage_queue,
    expand_dot_properties,
    load_runtime_settings,
    parse_csv_list,
)
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings, queue_settings, datahub_settings = load_runtime_settings()
    lineage_client = build_datahub_lineage_client(
        datahub_settings=datahub_settings,
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan"),
    )

    raw_config = expand_dot_properties(lineage_client.stage_config.custom_properties)
    scan_config, queue_config = _extract_scan_and_queue_config(raw_config)
    extensions = parse_csv_list(scan_config["filters"]["extensions"])

    stage_queue = build_stage_queue(
        broker_url=queue_settings.broker_url,
        queue_config=queue_config,
    )
    object_storage = build_object_storage(s3_settings)

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

def _extract_scan_and_queue_config(expanded_config: dict) -> tuple[dict, dict]:
    """Return scan and queue config sections from expanded properties."""
    return expanded_config["scan"], expanded_config["queue"]


if __name__ == "__main__":
    run()
