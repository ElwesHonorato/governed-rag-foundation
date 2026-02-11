PROCESSING_CONFIG_DEFAULT = {
    "poll_interval_seconds": 30,
    "queue": {
        "parse_queue": "q.parse_document",
        "parse_dlq_queue": "q.parse_document.dlq",
        "chunk_text_queue": "q.chunk_text",
    },
    "storage": {
        "bucket": "rag-data",
        "raw_prefix": "02_raw/",
        "processed_prefix": "03_processed/",
    },
    "security": {"clearance": "internal"},
}
