import json
from typing import Any

from chunking.domain.text_chunker import chunk_text
from pipeline_common.helpers.contracts import chunk_id_for


class ChunkTextProcessor:
    """Build chunk records from parsed document payload."""

    def __init__(
        self,
        *,
        spark_session: Any | None,
    ) -> None:
        self.spark_session = spark_session

    @staticmethod
    def read_processed_payload(raw_payload: bytes) -> dict[str, Any]:
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def build_chunk_records(self, processed: dict[str, Any], doc_id: str) -> list[dict[str, Any]]:
        parsed_payload = processed.get("parsed")
        parsed_text = parsed_payload.get("text", "") if isinstance(parsed_payload, dict) else ""
        chunks = chunk_text(str(parsed_text or processed.get("text", "")))
        records: list[dict[str, Any]] = []
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
        return records
