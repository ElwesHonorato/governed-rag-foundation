"""Worker runtime context model."""

from dataclasses import dataclass
from typing import Any

from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import QueueGateway


@dataclass(frozen=True)
class WorkerRuntimeContext:
    """Runtime dependencies resolved by startup bootstrap."""

    lineage_gateway: LineageRuntimeGateway
    object_storage_gateway: ObjectStorageGateway | None
    stage_queue_gateway: QueueGateway | None
    spark_session: Any | None
    job_properties: dict[str, Any]
