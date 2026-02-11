from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES


EMBED_CHUNKS_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "storage": {
        "bucket": "rag-data",
        "chunks_prefix": "04_chunks/",
        "embeddings_prefix": "05_embeddings/",
    },
    "queue": {
        "stage": "embed_chunks",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
}
