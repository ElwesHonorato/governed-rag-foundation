PROCESSING_CONFIG_DEFAULT = {
    "poll_interval_seconds": 30,
    "queue": {
        "parse": "q.parse_document",
        "chunk_text": "q.chunk_text",
        "parse_dlq": "q.parse_document.dlq",
    },
    "storage": {
        "bucket": "rag-data",
        "raw_prefix": "02_raw/",
        "processed_prefix": "03_processed/",
    },
    "security": {"clearance": "internal"},
}
