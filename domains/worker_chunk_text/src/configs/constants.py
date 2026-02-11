from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

S3_BUCKET = "rag-data"

QUEUE_CONFIG_DEFAULT = {
    "stage": "chunk_text",
    "stage_queues": WORKER_STAGE_QUEUES,
    "queue_pop_timeout_seconds": 1,
}
