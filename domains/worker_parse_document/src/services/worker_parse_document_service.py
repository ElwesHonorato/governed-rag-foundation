
import time

from pipeline_common.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store
from parsing.registry import parser_for_key


class WorkerParseDocumentService:
    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        s3: S3Store,
        s3_bucket: str,
        poll_interval_seconds: int,
        source_type: str,
        security_clearance: str,
    ) -> None:
        self.stage_queue = stage_queue
        self.s3 = s3
        self.s3_bucket = s3_bucket
        self.poll_interval_seconds = poll_interval_seconds
        self.source_type = source_type
        self.security_clearance = security_clearance

    def process_source_key(self, source_key: str) -> None:
        if not source_key.startswith("02_raw/"):
            return
        if not source_key.endswith((".html", ".htm")):
            return

        doc_id = doc_id_from_source_key(source_key)
        destination_key = f"03_processed/{doc_id}.json"
        if self.s3.object_exists(self.s3_bucket, destination_key):
            return

        parser = parser_for_key(source_key)
        parsed = parser.parse(self.s3.read_text(self.s3_bucket, source_key))
        payload = {
            "doc_id": doc_id,
            "source_key": source_key,
            "source_type": self.source_type,
            "timestamp": utc_now_iso(),
            "security_clearance": self.security_clearance,
            "title": parsed["title"],
            "text": parsed["text"],
        }
        self.s3.write_json(self.s3_bucket, destination_key, payload)
        self.stage_queue.push("q.chunk_text", {"processed_key": destination_key, "doc_id": doc_id})
        print(f"[worker_parse_document] wrote {destination_key}", flush=True)

    def run_forever(self) -> None:
        while True:
            queued = self.stage_queue.pop("q.parse_document", timeout_seconds=1)
            if queued and isinstance(queued.get("raw_key"), str):
                self.process_source_key(str(queued["raw_key"]))
            else:
                keys = [
                    key
                    for key in self.s3.list_keys(self.s3_bucket, "02_raw/")
                    if key != "02_raw/" and key.endswith((".html", ".htm"))
                ]
                for source_key in keys:
                    self.process_source_key(source_key)

            time.sleep(self.poll_interval_seconds)
