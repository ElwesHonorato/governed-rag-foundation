from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

CHUNK_TEXT_PROCESSING_CONFIG = {
    "storage": {"bucket": "rag-data"},
    "queue": {
        "stage": "chunk_text",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
}

S3_BUCKET = CHUNK_TEXT_PROCESSING_CONFIG["storage"]["bucket"]
