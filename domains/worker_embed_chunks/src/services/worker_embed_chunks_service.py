from __future__ import annotations

import hashlib
import time

from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store


class WorkerEmbedChunksService:
    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        s3: S3Store,
        s3_bucket: str,
        poll_interval_seconds: int,
        dimension: int,
    ) -> None:
        self.stage_queue = stage_queue
        self.s3 = s3
        self.s3_bucket = s3_bucket
        self.poll_interval_seconds = poll_interval_seconds
        self.dimension = dimension

    def deterministic_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(self.dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

    def process_source_key(self, source_key: str) -> None:
        if not source_key.startswith("04_chunks/"):
            return
        if not source_key.endswith(".chunks.json"):
            return

        payload = self.s3.read_json(self.s3_bucket, source_key)
        doc_id = str(payload["doc_id"])
        destination_key = f"05_embeddings/{doc_id}.embeddings.json"
        if self.s3.object_exists(self.s3_bucket, destination_key):
            return

        records = []
        for chunk in payload.get("chunks", []):
            text = str(chunk["chunk_text"])
            records.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "vector": self.deterministic_embedding(text),
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

        self.s3.write_json(self.s3_bucket, destination_key, {"doc_id": doc_id, "embeddings": records})
        self.stage_queue.push("q.index_weaviate", {"embeddings_key": destination_key, "doc_id": doc_id})
        print(f"[worker_embed_chunks] wrote {destination_key} embeddings={len(records)}", flush=True)

    def run_forever(self) -> None:
        while True:
            queued = self.stage_queue.pop("q.embed_chunks", timeout_seconds=1)
            if queued and isinstance(queued.get("chunks_key"), str):
                self.process_source_key(str(queued["chunks_key"]))
            else:
                keys = [
                    key
                    for key in self.s3.list_keys(self.s3_bucket, "04_chunks/")
                    if key != "04_chunks/" and key.endswith(".chunks.json")
                ]
                for source_key in keys:
                    self.process_source_key(source_key)

            time.sleep(self.poll_interval_seconds)
