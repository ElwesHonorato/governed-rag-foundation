from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES


PARSE_DOCUMENT_PROCESSING_CONFIG = {
    "queue": {
        "stage": "parse_document",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
    "storage": {
        "bucket": "rag-data",
        "raw_prefix": "02_raw/",
        "processed_prefix": "03_processed/",
    },
    "security": {"clearance": "internal"},
}
