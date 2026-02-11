from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES


QUEUE_CONFIG_DEFAULT = {
    "stage": "parse_document",
    "stage_queues": WORKER_STAGE_QUEUES,
    "queue_pop_timeout_seconds": 1,
}

PROCESSING_CONFIG_DEFAULT = {
    "storage": {
        "bucket": "rag-data",
        "raw_prefix": "02_raw/",
        "processed_prefix": "03_processed/",
    },
    "security": {"clearance": "internal"},
}
