MANIFEST_PROCESSING_CONFIG = {

    "poll_interval_seconds": 30,
    "storage": {
        "bucket": "rag-data",
        "processed_prefix": "03_processed/",
        "chunks_prefix": "04_chunks/",
        "embeddings_prefix": "05_embeddings/",
        "indexes_prefix": "06_indexes/",
        "manifest_prefix": "07_metadata/manifest/",
    },
}
