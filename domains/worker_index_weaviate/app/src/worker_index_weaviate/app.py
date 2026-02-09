from __future__ import annotations

import time

from pipeline_common.config import WorkerIndexWeaviateSettings
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client
from pipeline_common.weaviate import ensure_schema, upsert_chunk, verify_query


def run() -> None:
    settings = WorkerIndexWeaviateSettings.from_env()
    stage_queue = StageQueue(settings.redis_url)
    s3 = S3Store(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    s3.ensure_workspace(settings.s3_bucket)
    ensure_schema(settings.weaviate_url)

    def process_source_key(source_key: str) -> None:
        if not source_key.startswith("05_embeddings/"):
            return
        if not source_key.endswith(".embeddings.json"):
            return

        payload = s3.read_json(settings.s3_bucket, source_key)
        for item in payload.get("embeddings", []):
            metadata = dict(item.get("metadata", {}))
            chunk_id = str(item["chunk_id"])
            vector = item.get("vector", [])
            upsert_chunk(
                settings.weaviate_url,
                chunk_id=chunk_id,
                vector=vector,
                properties={
                    "chunk_id": chunk_id,
                    "doc_id": metadata.get("doc_id"),
                    "chunk_text": metadata.get("chunk_text"),
                    "source_key": metadata.get("source_key"),
                    "security_clearance": metadata.get("security_clearance"),
                },
            )

        doc_id = payload.get("doc_id", "unknown")
        s3.write_json(settings.s3_bucket, f"06_indexes/{doc_id}.indexed.json", {"doc_id": doc_id, "status": "indexed"})
        result = verify_query(settings.weaviate_url, "logistics")
        print(f"[worker_index_weaviate] indexed doc_id={doc_id} verify={bool(result)}", flush=True)

    while True:
        queued = stage_queue.pop("q.index_weaviate", timeout_seconds=1)
        if queued and isinstance(queued.get("embeddings_key"), str):
            process_source_key(str(queued["embeddings_key"]))
        else:
            keys = [
                key
                for key in s3.list_keys(settings.s3_bucket, "05_embeddings/")
                if key != "05_embeddings/" and key.endswith(".embeddings.json")
            ]
            for source_key in keys:
                process_source_key(source_key)

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run()
