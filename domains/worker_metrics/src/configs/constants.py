METRICS_PROCESSING_CONFIG = {
    "poll_interval_seconds": 30,
    "storage": {"bucket": "rag-data"},
}

S3_BUCKET = METRICS_PROCESSING_CONFIG["storage"]["bucket"]
