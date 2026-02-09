from __future__ import annotations

import os
import time

from pipeline_common.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.config import Settings
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store, build_s3_client
from worker_parse_document.parsing.registry import parser_for_key


def run() -> None:
    settings = Settings()
    stage_queue = StageQueue(settings.redis_url)
    source_type = os.getenv("SOURCE_TYPE", "html")
    security_clearance = os.getenv("DEFAULT_SECURITY_CLEARANCE", "internal")

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
        if not source_key.startswith("02_raw/"):
            return
        if not source_key.endswith((".html", ".htm")):
            return

        doc_id = doc_id_from_source_key(source_key)
        destination_key = f"03_processed/{doc_id}.json"
        if s3.object_exists(settings.s3_bucket, destination_key):
            return

        parser = parser_for_key(source_key)
        parsed = parser.parse(s3.read_text(settings.s3_bucket, source_key))
        payload = {
            "doc_id": doc_id,
            "source_key": source_key,
            "source_type": source_type,
            "timestamp": utc_now_iso(),
            "security_clearance": security_clearance,
            "title": parsed["title"],
            "text": parsed["text"],
        }
        s3.write_json(settings.s3_bucket, destination_key, payload)
        stage_queue.push("q.chunk_text", {"processed_key": destination_key, "doc_id": doc_id})
        print(f"[worker_parse_document] wrote {destination_key}", flush=True)

    while True:
        queued = stage_queue.pop("q.parse_document", timeout_seconds=1)
        if queued and isinstance(queued.get("raw_key"), str):
            process_source_key(str(queued["raw_key"]))
        else:
            keys = [
                key
                for key in s3.list_keys(settings.s3_bucket, "02_raw/")
                if key != "02_raw/" and key.endswith((".html", ".htm"))
            ]
            for source_key in keys:
                process_source_key(source_key)

        time.sleep(settings.poll_interval_seconds)


if __name__ == "__main__":
    run()
