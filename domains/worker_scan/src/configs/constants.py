from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

SCAN_PROCESSING_CONFIG = {
    "storage": {
        "bucket": "rag-data",
        "incoming_prefix": "01_incoming/",
        "raw_prefix": "02_raw/",
    },
    "filters": {"extensions": [".html"]},
    "queue": {
        "stage": "scan",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
}

S3_BUCKET = SCAN_PROCESSING_CONFIG["storage"]["bucket"]
INCOMING_PREFIX = SCAN_PROCESSING_CONFIG["storage"]["incoming_prefix"]
RAW_PREFIX = SCAN_PROCESSING_CONFIG["storage"]["raw_prefix"]
HTML_EXTENSIONS = SCAN_PROCESSING_CONFIG["filters"]["extensions"]
