PROCESSING_CONFIG_DEFAULT = {
    "queue_pop_timeout_seconds": 1,
    "storage": {
        "bucket": "rag-data",
        "raw_prefix": "02_raw/",
        "processed_prefix": "03_processed/",
    },
    "security": {"clearance": "internal"},
}
