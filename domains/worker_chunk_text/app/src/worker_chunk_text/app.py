from __future__ import annotations

import time

from pipeline_common.config import Settings
from pipeline_common.contracts import chunk_id_for
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client
from pipeline_common.text import chunk_text


def run() -> None:
    settings = Settings()
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

    def process_source_key(source_key: str) -> None:
        if not source_key.startswith("03_processed/"):
            return
        if not source_key.endswith(".json"):
            return

        processed = s3.read_json(settings.s3_bucket, source_key)
        doc_id = str(processed["doc_id"])
        destination_key = f"04_chunks/{doc_id}.chunks.json"
        if s3.object_exists(settings.s3_bucket, destination_key):
            return

        chunks = chunk_text(str(processed.get("text", "")))
        records = []
        for index, chunk in enumerate(chunks):
            records.append(
                {
                    "chunk_id": chunk_id_for(doc_id, index, chunk),
                    "doc_id": doc_id,
                    "chunk_index": index,
                    "chunk_text": chunk,
                    "source_type": processed.get("source_type", "html"),
                    "timestamp": processed.get("timestamp"),
                    "security_clearance": processed.get("security_clearance", "internal"),
                    "source_key": processed.get("source_key"),
                }
            )

        s3.write_json(settings.s3_bucket, destination_key, {"doc_id": doc_id, "chunks": records})
        stage_queue.push("q.embed_chunks", {"chunks_key": destination_key, "doc_id": doc_id})
        print(f"[worker_chunk_text] wrote {destination_key} chunks={len(records)}", flush=True)

    while True:
        queued = stage_queue.pop("q.chunk_text", timeout_seconds=1)
        if queued and isinstance(queued.get("processed_key"), str):
            process_source_key(str(queued["processed_key"]))
        else:
            keys = [
                key
                for key in s3.list_keys(settings.s3_bucket, "03_processed/")
                if key != "03_processed/" and key.endswith(".json")
            ]
            for source_key in keys:
                process_source_key(source_key)

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run()
