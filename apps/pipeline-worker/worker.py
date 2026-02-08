import os
import time


while True:
    print(
        "pipeline-worker heartbeat",
        {
            "weaviate": os.getenv("WEAVIATE_URL"),
            "redis": os.getenv("REDIS_URL"),
            "s3": os.getenv("S3_ENDPOINT"),
            "marquez": os.getenv("MARQUEZ_URL"),
        },
        flush=True,
    )
    time.sleep(30)
