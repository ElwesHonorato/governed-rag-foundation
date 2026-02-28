"""Worker runtime context model."""

from dataclasses import dataclass
from typing import Any

from pipeline_common.lineage.data_hub import DataHubRunTimeLineage
from pipeline_common.object_storage import ObjectStorageGateway
from pipeline_common.queue import StageQueue


@dataclass(frozen=True)
class WorkerRuntimeContext:
    """Runtime dependencies resolved by startup bootstrap."""

    lineage_gateway: DataHubRunTimeLineage
    object_storage_gateway: ObjectStorageGateway
    stage_queue_gateway: StageQueue
    job_properties: dict[str, Any]
