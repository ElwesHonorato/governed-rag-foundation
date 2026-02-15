from pipeline_common.config import JobStageName, LineageDatasetNamespace
from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

PARSE_DOCUMENT_STORAGE_BUCKET = "rag-data"


PARSE_DOCUMENT_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "queue": {
        "stage": "parse_document",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
    "storage": {
        "bucket": PARSE_DOCUMENT_STORAGE_BUCKET,
        "raw_prefix": "02_raw/",
        "processed_prefix": "03_processed/",
    },
    "security": {"clearance": "internal"},
    "lineage": {
        "job_stage": JobStageName.WORKER_PARSE_DOCUMENT,
        "producer": "https://github.com/ElwesHonorato/governed-rag-foundation",
        "dataset_namespace": LineageDatasetNamespace.GOVERNED_RAG_DATA,
    },
}
