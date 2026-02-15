from pipeline_common.config import JobStageName, LineageDatasetNamespace
from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

EMBED_CHUNKS_STORAGE_BUCKET = "rag-data"

EMBED_CHUNKS_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "storage": {
        "bucket": EMBED_CHUNKS_STORAGE_BUCKET,
        "chunks_prefix": "04_chunks/",
        "embeddings_prefix": "05_embeddings/",
    },
    "queue": {
        "stage": "embed_chunks",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
    "lineage": {
        "job_stage": JobStageName.WORKER_EMBED_CHUNKS,
        "producer": "https://github.com/ElwesHonorato/governed-rag-foundation",
        "dataset_namespace": LineageDatasetNamespace.GOVERNED_RAG_DATA,
    },
}
