from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

EMBED_CHUNKS_PROCESSING_CONFIG = {
    "storage": {"bucket": "rag-data"},
    "queue": {
        "stage": "embed_chunks",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
}

S3_BUCKET = EMBED_CHUNKS_PROCESSING_CONFIG["storage"]["bucket"]
