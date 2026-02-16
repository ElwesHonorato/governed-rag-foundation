from pipeline_common.config import JobStageName
from pipeline_common.lineage import LineageEmitterConfig
from pipeline_common.lineage.constants import LineageNamespace
from pipeline_common.queue.contracts import WORKER_STAGE_QUEUES

INDEX_WEAVIATE_STORAGE_BUCKET = "rag-data"
INDEX_WEAVIATE_LINEAGE_CONFIG = LineageEmitterConfig(
    namespace=LineageNamespace.GOVERNED_RAG,
    job_stage=JobStageName.WORKER_INDEX_WEAVIATE,
    dataset_namespace=INDEX_WEAVIATE_STORAGE_BUCKET,
    producer="https://github.com/ElwesHonorato/governed-rag-foundation",
    timeout_seconds=3.0,
)

INDEX_WEAVIATE_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "storage": {
        "bucket": INDEX_WEAVIATE_STORAGE_BUCKET,
        "embeddings_prefix": "05_embeddings/",
        "indexes_prefix": "06_indexes/",
    },
    "queue": {
        "stage": "index_weaviate",
        "stage_queues": WORKER_STAGE_QUEUES,
        "queue_pop_timeout_seconds": 1,
    },
    "lineage": INDEX_WEAVIATE_LINEAGE_CONFIG,
}
