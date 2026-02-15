from pipeline_common.config import JobStageName, LineageDatasetNamespace
from pipeline_common.lineage import LineageEmitterConfig
from pipeline_common.lineage.constants import LineageNamespace
from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

CHUNK_TEXT_STORAGE_BUCKET = "rag-data"
CHUNK_TEXT_LINEAGE_CONFIG = LineageEmitterConfig(
    namespace=LineageNamespace.GOVERNED_RAG,
    job_stage=JobStageName.WORKER_CHUNK_TEXT,
    producer="https://github.com/ElwesHonorato/governed-rag-foundation",
    dataset_namespace=LineageDatasetNamespace.GOVERNED_RAG_DATA,
    timeout_seconds=3.0,
)

CHUNK_TEXT_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "storage": {
        "bucket": CHUNK_TEXT_STORAGE_BUCKET,
        "processed_prefix": "03_processed/",
        "chunks_prefix": "04_chunks/",
    },
    "queue": {
        "stage": "chunk_text",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
    "lineage": CHUNK_TEXT_LINEAGE_CONFIG,
}
