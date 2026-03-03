import json
from typing import Any


class ManifestCycleProcessor:
    """Build manifest status payloads from stage presence signals."""

    def __init__(
        self,
        *,
        processed_prefix: str,
        manifest_prefix: str,
        spark_session: Any | None,
    ) -> None:
        self.processed_prefix = processed_prefix
        self.manifest_prefix = manifest_prefix
        self.spark_session = spark_session

    def list_doc_ids(self, processed_keys: list[str]) -> list[str]:
        return [
            key.split("/")[-1].replace(".json", "")
            for key in processed_keys
            if key != self.processed_prefix and key.endswith(".json")
        ]

    @staticmethod
    def any_stage_object_exists(stage_keys: list[str], doc_prefix: str, suffixes: tuple[str, ...]) -> bool:
        return any(key != doc_prefix and key.endswith(suffixes) for key in stage_keys)

    def build_manifest_key(self, doc_id: str) -> str:
        return f"{self.manifest_prefix}{doc_id}.json"

    @staticmethod
    def build_manifest_status(
        *,
        doc_id: str,
        parse_document: bool,
        chunk_text: bool,
        embed_chunks: bool,
        index_weaviate: bool,
    ) -> bytes:
        status = {
            "doc_id": doc_id,
            "stages": {
                "parse_document": parse_document,
                "chunk_text": chunk_text,
                "embed_chunks": embed_chunks,
                "index_weaviate": index_weaviate,
            },
            "attempts": 1,
            "last_error": None,
        }
        return json.dumps(status, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
