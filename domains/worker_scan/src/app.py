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

from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any

from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.startup import (
    WorkerRuntimeLauncher,
    WorkerConfigExtractor,
    WorkerServiceFactory,
    WorkerRuntimeContext,
)
from services.scan_cycle_processor import ScanStorageContract, StorageScanCycleProcessor
from services.worker_scan_service import ScanPollingContract, WorkerScanService


@dataclass(frozen=True)
class ScanWorkerConfig:
    """Typed scan worker startup configuration."""

    bucket: str
    incoming_prefix: str
    raw_prefix: str
    poll_interval_seconds: int
    queue_config: dict[str, Any]


def run() -> None:
    """Start scan worker using class-based bootstrap template."""
    WorkerRuntimeLauncher[ScanWorkerConfig, WorkerScanService](
        data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan"),
        config_extractor=ScanConfigExtractor(),
        service_factory=ScanServiceFactory(),
    ).start()


class ScanConfigExtractor(WorkerConfigExtractor[ScanWorkerConfig]):
    """Parse and validate worker_scan config from DataHub job properties."""

    def extract(self, job_properties: Mapping[str, Any]) -> ScanWorkerConfig:
        """Extract typed scan worker config."""
        job_config = job_properties["job"]
        queue_config = job_config["queue"]
        return ScanWorkerConfig(
            bucket=job_config["storage"]["bucket"],
            incoming_prefix=job_config["storage"]["incoming_prefix"],
            raw_prefix=job_config["storage"]["raw_prefix"],
            poll_interval_seconds=int(job_config["poll_interval_seconds"]),
            queue_config=queue_config,
        )


class ScanServiceFactory(WorkerServiceFactory[ScanWorkerConfig, WorkerScanService]):
    """Build scan service from runtime context and typed scan config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: ScanWorkerConfig,
    ) -> WorkerScanService:
        """Construct worker scan service object graph."""
        stage_queue = runtime.stage_queue_gateway
        object_storage = runtime.object_storage_gateway
        lineage_gateway = runtime.lineage_gateway

        # Keep startup side effect explicit and early.
        object_storage.bootstrap_bucket_prefixes(worker_config.bucket)

        processor = StorageScanCycleProcessor(
            object_storage=object_storage,
            stage_queue=stage_queue,
            lineage=lineage_gateway,
            storage_contract=ScanStorageContract(
                bucket=worker_config.bucket,
                incoming_prefix=worker_config.incoming_prefix,
                raw_prefix=worker_config.raw_prefix,
            ),
        )
        return WorkerScanService(
            processor=processor,
            polling_contract=ScanPollingContract(
                poll_interval_seconds=worker_config.poll_interval_seconds,
            ),
        )


if __name__ == "__main__":
    run()
