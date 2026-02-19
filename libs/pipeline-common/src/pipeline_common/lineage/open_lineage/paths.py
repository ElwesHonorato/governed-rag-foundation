def s3_uri(bucket: str, key: str) -> str:
    """Build one canonical S3 URI from bucket and object key."""
    return f"s3://{bucket}/{key.lstrip('/')}"
