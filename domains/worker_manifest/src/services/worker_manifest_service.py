from __future__ import annotations

import time

from pipeline_common.s3 import S3Store, build_s3_client
from configs.configs import WorkerS3LoopSettings


class WorkerManifestService:
    def __init__(self, *, settings: WorkerS3LoopSettings, s3: S3Store) -> None:
        self.settings = settings
        self.s3 = s3

    @classmethod
    def from_env(cls) -> "WorkerManifestService":
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
        return cls(settings=settings, s3=s3)

    def run_forever(self) -> None:
        while True:
            processed_keys = [
                key
                for key in self.s3.list_keys(self.settings.s3_bucket, "03_processed/")
                if key != "03_processed/" and key.endswith(".json")
            ]

            for processed_key in processed_keys:
                doc_id = processed_key.split("/")[-1].replace(".json", "")
                manifest_key = f"07_metadata/manifest/{doc_id}.json"

                status = {
                    "doc_id": doc_id,
                    "stages": {
                        "parse_document": self.s3.object_exists(self.settings.s3_bucket, f"03_processed/{doc_id}.json"),
                        "chunk_text": self.s3.object_exists(self.settings.s3_bucket, f"04_chunks/{doc_id}.chunks.json"),
                        "embed_chunks": self.s3.object_exists(self.settings.s3_bucket, f"05_embeddings/{doc_id}.embeddings.json"),
                        "index_weaviate": self.s3.object_exists(self.settings.s3_bucket, f"06_indexes/{doc_id}.indexed.json"),
                    },
                    "attempts": 1,
                    "last_error": None,
                }
                self.s3.write_json(self.settings.s3_bucket, manifest_key, status)

            time.sleep(self.settings.poll_interval_seconds)
