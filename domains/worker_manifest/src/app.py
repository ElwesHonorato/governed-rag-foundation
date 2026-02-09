from __future__ import annotations

import time

from pipeline_common.s3 import S3Store, build_s3_client
from configs.configs import WorkerS3LoopSettings


def run() -> None:
    settings = WorkerS3LoopSettings.from_env()
    s3 = S3Store(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    s3.ensure_workspace(settings.s3_bucket)

    while True:
        processed_keys = [
            key
            for key in s3.list_keys(settings.s3_bucket, "03_processed/")
            if key != "03_processed/" and key.endswith(".json")
        ]

        for processed_key in processed_keys:
            doc_id = processed_key.split("/")[-1].replace(".json", "")
            manifest_key = f"07_metadata/manifest/{doc_id}.json"

            status = {
                "doc_id": doc_id,
                "stages": {
                    "parse_document": s3.object_exists(settings.s3_bucket, f"03_processed/{doc_id}.json"),
                    "chunk_text": s3.object_exists(settings.s3_bucket, f"04_chunks/{doc_id}.chunks.json"),
                    "embed_chunks": s3.object_exists(settings.s3_bucket, f"05_embeddings/{doc_id}.embeddings.json"),
                    "index_weaviate": s3.object_exists(settings.s3_bucket, f"06_indexes/{doc_id}.indexed.json"),
                },
                "attempts": 1,
                "last_error": None,
            }
            s3.write_json(settings.s3_bucket, manifest_key, status)

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run()
