from pipeline_common.config import JobStageName
from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES


CHUNK_TEXT_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "storage": {
        "bucket": "rag-data",
        "processed_prefix": "03_processed/",
        "chunks_prefix": "04_chunks/",
    },
    "queue": {
        "stage": "chunk_text",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
    "lineage": {
        "job_stage": JobStageName.WORKER_CHUNK_TEXT,
        "producer": "https://github.com/ElwesHonorato/governed-rag-foundation",
    },
}
