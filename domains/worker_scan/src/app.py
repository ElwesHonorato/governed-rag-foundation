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

from pipeline_common.lineage.contracts import DataHubDataJobKey
from pipeline_common.lineage.pipeline import DataHubPipelineJobs
from pipeline_common.startup import (
    InfrastructureFactory,
    JobPropertiesParser,
    RuntimeContextFactory,
    WorkerBootstrap,
    WorkerConfigExtractor,
    WorkerServiceFactory,
    WorkerRuntimeContext,
)
from services.scan_cycle_processor import StorageScanCycleProcessor
from services.worker_scan_service import WorkerScanService


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
    ScanWorkerBootstrap().run()


class ScanConfigExtractor(WorkerConfigExtractor[ScanWorkerConfig]):
    """Parse and validate worker_scan config from DataHub job properties."""

    def extract(self, custom_properties: Mapping[str, str]) -> ScanWorkerConfig:
        """Extract typed scan worker config."""
        properties_parser = JobPropertiesParser(custom_properties)
        raw_config = properties_parser.job_properties
        job_config = raw_config["job"]
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
        infrastructure: InfrastructureFactory,
        worker_config: ScanWorkerConfig,
    ) -> WorkerScanService:
        """Construct worker scan service object graph."""
        stage_queue = infrastructure.stage_queue
        object_storage = infrastructure.object_storage

        # Keep startup side effect explicit and early.
        object_storage.bootstrap_bucket_prefixes(worker_config.bucket)

        processor = StorageScanCycleProcessor(
            object_storage=object_storage,
            stage_queue=stage_queue,
            lineage=infrastructure.datahub_lineage_client,
            processing_config={
                "storage": {
                    "bucket": worker_config.bucket,
                    "incoming_prefix": worker_config.incoming_prefix,
                    "raw_prefix": worker_config.raw_prefix,
                },
            },
        )
        return WorkerScanService(
            processor=processor,
            processing_config={"poll_interval_seconds": worker_config.poll_interval_seconds},
        )


class ScanWorkerBootstrap(WorkerBootstrap[ScanWorkerConfig, WorkerScanService]):
    """Concrete worker bootstrap for worker_scan."""

    def __init__(self) -> None:
        super().__init__(runtime_factory=RuntimeContextFactory(data_job_key=DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan")))
        self._extractor = ScanConfigExtractor()
        self._factory = ScanServiceFactory()

    def data_job_key(self) -> DataHubDataJobKey:
        """Return DataHub job key for worker_scan."""
        return DataHubPipelineJobs.CUSTOM_GOVERNED_RAG.job("worker_scan")

    def config_extractor(self) -> WorkerConfigExtractor[ScanWorkerConfig]:
        """Return scan config extractor."""
        return self._extractor

    def service_factory(self) -> WorkerServiceFactory[ScanWorkerConfig, WorkerScanService]:
        """Return scan service factory."""
        return self._factory


if __name__ == "__main__":
    run()
