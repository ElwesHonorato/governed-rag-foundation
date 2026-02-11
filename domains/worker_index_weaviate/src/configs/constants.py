from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES


INDEX_WEAVIATE_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "storage": {
        "bucket": "rag-data",
        "embeddings_prefix": "05_embeddings/",
        "indexes_prefix": "06_indexes/",
    },
    "queue": {
        "stage": "index_weaviate",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
}
