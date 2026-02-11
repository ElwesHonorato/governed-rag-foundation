
from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

S3_BUCKET = "rag-data"
INCOMING_PREFIX = "01_incoming/"
RAW_PREFIX = "02_raw/"
HTML_EXTENSIONS = [".html"]

QUEUE_CONFIG_DEFAULT = {
    "stage": "scan",
    "stage_queues": WORKER_STAGE_QUEUES,
    "queue_pop_timeout_seconds": 1,
}
