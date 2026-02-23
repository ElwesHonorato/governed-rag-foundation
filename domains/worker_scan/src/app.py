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

from pipeline_common.queue import StageQueue

from pipeline_common.lineage.data_hub import DataHubLineageClient
from pipeline_common.lineage.data_hub.contracts import DataHubLineageRuntimeConfig
from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.object_storage import ObjectStorageGateway, S3Client
from pipeline_common.queue.contracts import QueueStorageKeyMessage
from pipeline_common.settings import (
    DataHubBootstrapSettings,
    QueueRuntimeSettings,
    S3StorageSettings,
)
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService


def _required_property(custom_properties: dict[str, str], key: str) -> str:
    value = custom_properties.get(key)
    if value is None or not str(value).strip():
        raise ValueError(f"Missing DataHub custom property '{key}' for worker_scan.")
    return str(value).strip()


def _build_processing_config(custom_properties: dict[str, str]) -> dict:
    poll_interval_seconds = int(_required_property(custom_properties, "scan.poll_interval_seconds"))
    queue_pop_timeout_seconds = int(_required_property(custom_properties, "queue.pop_timeout_seconds"))
    bucket = _required_property(custom_properties, "scan.storage.bucket")
    incoming_prefix = _required_property(custom_properties, "scan.storage.incoming_prefix")
    raw_prefix = _required_property(custom_properties, "scan.storage.raw_prefix")
    extensions_csv = _required_property(custom_properties, "scan.filters.extensions")
    extensions = [ext.strip() for ext in extensions_csv.split(",") if ext.strip()]
    if not extensions:
        raise ValueError("DataHub custom property 'scan.filters.extensions' cannot be empty.")
    return {
        "poll_interval_seconds": poll_interval_seconds,
        "storage": {
            "bucket": bucket,
            "incoming_prefix": incoming_prefix,
            "raw_prefix": raw_prefix,
        },
        "filters": {"extensions": extensions},
        "queue": {
            "queue_pop_timeout_seconds": queue_pop_timeout_seconds,
        },
    }


def _build_scan_queue_config(*, queue_pop_timeout_seconds: int, produce_queue: str, dlq_queue: str) -> dict:
    return {
        "stage": "scan",
        "stage_queues": {
            "scan": {
                "consume": {"queue_name": "", "queue_contract": dict},
                "produce": {"queue_name": produce_queue, "queue_contract": QueueStorageKeyMessage},
                "dlq": {"queue_name": dlq_queue, "queue_contract": QueueStorageKeyMessage},
            }
        },
        "queue_pop_timeout_seconds": queue_pop_timeout_seconds,
    }


def run() -> None:
    """Initialize dependencies and start the worker service."""
    s3_settings = S3StorageSettings.from_env()
    queue_settings = QueueRuntimeSettings.from_env()
    datahub_settings = DataHubBootstrapSettings.from_env()
    lineage = DataHubLineageClient(
        client_config=DataHubLineageRuntimeConfig(
            bootstrap_settings={
                "server": datahub_settings.server,
                "env": datahub_settings.env,
                "token": datahub_settings.token,
            },
            data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan"),
        )
    )
    processing_config = _build_processing_config(lineage.stage_config.custom_properties)
    if not lineage.stage_config.queue_produce:
        raise ValueError("Missing DataHub custom property 'queue.produce' for worker_scan.")
    if not lineage.stage_config.queue_dlq:
        raise ValueError("Missing DataHub custom property 'queue.dlq' for worker_scan.")
    stage_queue = StageQueue(
        queue_settings.broker_url,
        queue_config=_build_scan_queue_config(
            queue_pop_timeout_seconds=processing_config["queue"]["queue_pop_timeout_seconds"],
            produce_queue=lineage.stage_config.queue_produce,
            dlq_queue=lineage.stage_config.queue_dlq,
        ),
    )
    object_storage = ObjectStorageGateway(
        S3Client(
            endpoint_url=s3_settings.s3_endpoint,
            access_key=s3_settings.s3_access_key,
            secret_key=s3_settings.s3_secret_key,
            region_name=s3_settings.aws_region,
        )
    )
    object_storage.bootstrap_bucket_prefixes(processing_config["storage"]["bucket"])
    processor = StorageScanCycleProcessor(
        object_storage=object_storage,
        stage_queue=stage_queue,
        lineage=lineage,
        processing_config=processing_config,
    )
    WorkerScanService(
        processor=processor,
        processing_config=processing_config,
    ).serve()


if __name__ == "__main__":
    run()
