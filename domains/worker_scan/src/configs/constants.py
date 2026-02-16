from pipeline_common.config import JobStageName
from pipeline_common.lineage import LineageEmitterConfig
from pipeline_common.lineage.constants import LineageNamespace
from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

SCAN_STORAGE_BUCKET = "rag-data"
SCAN_LINEAGE_CONFIG = LineageEmitterConfig(
    namespace=LineageNamespace.GOVERNED_RAG,
    job_stage=JobStageName.WORKER_SCAN,
    producer="https://github.com/ElwesHonorato/governed-rag-foundation",
    timeout_seconds=3.0,
)

SCAN_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "storage": {
        "bucket": SCAN_STORAGE_BUCKET,
        "incoming_prefix": "01_incoming/",
        "raw_prefix": "02_raw/",
    },
    "filters": {"extensions": [".html"]},
    "queue": {
        "stage": "scan",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
    "lineage": SCAN_LINEAGE_CONFIG,
}

S3_BUCKET = SCAN_PROCESSING_CONFIG["storage"]["bucket"]
INCOMING_PREFIX = SCAN_PROCESSING_CONFIG["storage"]["incoming_prefix"]
RAW_PREFIX = SCAN_PROCESSING_CONFIG["storage"]["raw_prefix"]
HTML_EXTENSIONS = SCAN_PROCESSING_CONFIG["filters"]["extensions"]
