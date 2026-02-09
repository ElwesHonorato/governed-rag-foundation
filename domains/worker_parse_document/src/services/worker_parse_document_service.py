
from abc import ABC, abstractmethod
import time

from pipeline_common.contracts import doc_id_from_source_key, utc_now_iso
from pipeline_common.queue import StageQueue
from pipeline_common.s3 import S3Store
from parsing.registry import parser_for_key


class WorkerService(ABC):
    @abstractmethod
    def run_forever(self) -> None:
        """Run the worker loop indefinitely."""


class WorkerParseDocumentService(WorkerService):
    """Transform raw source documents into processed payloads."""

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
        """Initialize parse worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.s3 = s3
        self.s3_bucket = s3_bucket
        self.poll_interval_seconds = poll_interval_seconds
        self.source_type = source_type
        self.security_clearance = security_clearance

    def process_source_key(self, source_key: str) -> None:
        """Parse a single raw document key and publish downstream work."""
        if not self._is_supported_source_key(source_key):
            return

        doc_id = doc_id_from_source_key(source_key)
        destination_key = self._processed_key(doc_id)
        if self._processed_exists(destination_key):
            return

        payload = self._build_processed_payload(source_key, doc_id)
        self._write_processed_document(destination_key, payload)
        self._enqueue_chunking(destination_key, doc_id)
        print(f"[worker_parse_document] wrote {destination_key}", flush=True)

    def run_forever(self) -> None:
        """Run the parse worker loop by queue-first then S3-fallback polling."""
        while True:
            for source_key in self._next_source_keys():
                self.process_source_key(source_key)
            time.sleep(self.poll_interval_seconds)

    def _next_source_keys(self) -> list[str]:
        """Return source keys from queue first, then from S3 polling fallback."""
        queued = self.stage_queue.pop("q.parse_document", timeout_seconds=1)
        if queued and isinstance(queued.get("raw_key"), str):
            return [str(queued["raw_key"])]
        return [
            key
            for key in self.s3.list_keys(self.s3_bucket, "02_raw/")
            if self._is_supported_source_key(key)
        ]

    def _is_supported_source_key(self, source_key: str) -> bool:
        """Return whether a source key is in raw HTML format."""
        return source_key.startswith("02_raw/") and source_key != "02_raw/" and source_key.endswith(
            (".html", ".htm")
        )

    def _processed_key(self, doc_id: str) -> str:
        """Build the processed-stage key for a document id."""
        return f"03_processed/{doc_id}.json"

    def _processed_exists(self, destination_key: str) -> bool:
        """Return whether the processed output already exists."""
        return self.s3.object_exists(self.s3_bucket, destination_key)

    def _build_processed_payload(self, source_key: str, doc_id: str) -> dict[str, str]:
        """Parse a source document and map it into processed payload fields."""
        parser = parser_for_key(source_key)
        parsed = parser.parse(self.s3.read_text(self.s3_bucket, source_key))
        return {
            "doc_id": doc_id,
            "source_key": source_key,
            "source_type": self.source_type,
            "timestamp": utc_now_iso(),
            "security_clearance": self.security_clearance,
            "title": parsed["title"],
            "text": parsed["text"],
        }

    def _write_processed_document(self, destination_key: str, payload: dict[str, str]) -> None:
        """Persist parsed document payload into the processed S3 stage."""
        self.s3.write_json(self.s3_bucket, destination_key, payload)

    def _enqueue_chunking(self, destination_key: str, doc_id: str) -> None:
        """Publish chunking work for a newly produced processed document."""
        self.stage_queue.push("q.chunk_text", {"processed_key": destination_key, "doc_id": doc_id})
