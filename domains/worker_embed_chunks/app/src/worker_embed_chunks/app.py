from __future__ import annotations

import hashlib
import os
import time

from pipeline_common.config import WorkerS3QueueLoopSettings
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client


def deterministic_embedding(text: str, dimension: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    for index in range(dimension):
        byte = digest[index % len(digest)]
        values.append((byte / 255.0) * 2.0 - 1.0)
    return values


def run() -> None:
    settings = WorkerS3QueueLoopSettings.from_env()
    stage_queue = StageQueue(settings.redis_url)
    dimension = int(os.getenv("EMBEDDING_DIM", "32"))
    s3 = S3Store(
        build_s3_client(
            endpoint_url=settings.s3_endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            region_name=settings.aws_region,
        )
    )
    s3.ensure_workspace(settings.s3_bucket)

    def process_source_key(source_key: str) -> None:
        if not source_key.startswith("04_chunks/"):
            return
        if not source_key.endswith(".chunks.json"):
            return

        payload = s3.read_json(settings.s3_bucket, source_key)
        doc_id = str(payload["doc_id"])
        destination_key = f"05_embeddings/{doc_id}.embeddings.json"
        if s3.object_exists(settings.s3_bucket, destination_key):
            return

        records = []
        for chunk in payload.get("chunks", []):
            text = str(chunk["chunk_text"])
            records.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "vector": deterministic_embedding(text, dimension),
                    "metadata": {
                        "source_type": chunk.get("source_type"),
                        "timestamp": chunk.get("timestamp"),
                        "security_clearance": chunk.get("security_clearance"),
                        "doc_id": chunk.get("doc_id"),
                        "source_key": chunk.get("source_key"),
                        "chunk_index": chunk.get("chunk_index"),
                        "chunk_text": text,
                    },
                }
            )

        s3.write_json(settings.s3_bucket, destination_key, {"doc_id": doc_id, "embeddings": records})
        stage_queue.push("q.index_weaviate", {"embeddings_key": destination_key, "doc_id": doc_id})
        print(f"[worker_embed_chunks] wrote {destination_key} embeddings={len(records)}", flush=True)

    while True:
        queued = stage_queue.pop("q.embed_chunks", timeout_seconds=1)
        if queued and isinstance(queued.get("chunks_key"), str):
            process_source_key(str(queued["chunks_key"]))
        else:
            keys = [
                key
                for key in s3.list_keys(settings.s3_bucket, "04_chunks/")
                if key != "04_chunks/" and key.endswith(".chunks.json")
            ]
            for source_key in keys:
                process_source_key(source_key)

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run()
