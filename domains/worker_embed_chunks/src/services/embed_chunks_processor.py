import hashlib
import json
from dataclasses import dataclass
from typing import Any

from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.provenance import embedding_params_hash

EMBEDDER_NAME = "deterministic_sha256"
EMBEDDER_VERSION = "1.0.0"


@dataclass(frozen=True)
class EmbeddingWriteResult:
    destination_key: str
    doc_id: str
    chunk_id: str
    wrote: bool


@dataclass(frozen=True)
class ChunkRecordPayload:
    index: int
    chunk_id: str
    chunk_text: str
    offsets_start: int
    offsets_end: int
    chunk_text_hash: str


@dataclass(frozen=True)
class ChunkArtifactPayload:
    chunk_record: ChunkRecordPayload
    destination_key: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, destination_key: str) -> "ChunkArtifactPayload":
        return cls(
            chunk_record=ChunkRecordPayload(**dict(payload)),
            destination_key=destination_key,
        )


class EmbedChunksProcessor:
    """Build embedding payloads from chunk payloads and write outputs."""

    def __init__(
        self,
        *,
        dimension: int,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        self.dimension = dimension
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix

    @staticmethod
    def _deterministic_embedding_for(text: str, dimension: int) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

    @staticmethod
    def read_chunk_payload(raw_payload: bytes, *, source_key: str) -> ChunkArtifactPayload:
        payload = dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))
        return ChunkArtifactPayload.from_dict(payload, destination_key=source_key)

    def write_embedding_artifact(
        self,
        payload: ChunkArtifactPayload,
        *,
        embedding_run_id: str,
    ) -> EmbeddingWriteResult:
        embedding_payload = self._build_embedding_payload_local(payload, embedding_run_id=embedding_run_id)
        return self._write_embedding_payload(embedding_payload)

    def _write_embedding_payload(self, embedding_payload: dict[str, Any]) -> EmbeddingWriteResult:
        doc_id = str(embedding_payload["doc_id"])
        chunk_id = str(embedding_payload["chunk_id"])
        destination_key = self._embedding_object_key(doc_id, chunk_id)
        if self.object_storage.object_exists(self.storage_bucket, destination_key):
            return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=False)
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(embedding_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )
        return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=True)

    def _build_embedding_payload_local(
        self,
        payload: ChunkArtifactPayload,
        *,
        embedding_run_id: str,
    ) -> dict[str, Any]:
        text = payload.chunk_record.chunk_text
        doc_id = self._doc_id_from_destination_key(payload.destination_key)
        chunk_id = payload.chunk_record.chunk_id
        embedder_params = {"dimension": int(self.dimension)}
        return {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": self._deterministic_embedding_for(text, self.dimension),
            "metadata": self._metadata_from_payload(
                source_type=None,
                timestamp=None,
                security_clearance=None,
                doc_id=doc_id,
                source_key=payload.destination_key,
                chunk_index=payload.chunk_record.index,
                text=text,
                run_id="",
                embedder_name=EMBEDDER_NAME,
                embedder_version=EMBEDDER_VERSION,
                embedding_params_hash=embedding_params_hash(embedder_params),
                embedding_run_id=embedding_run_id,
            ),
        }

    @staticmethod
    def _metadata_from_payload(
        *,
        source_type: Any,
        timestamp: Any,
        security_clearance: Any,
        doc_id: str,
        source_key: Any,
        chunk_index: Any,
        text: str,
        run_id: str,
        embedder_name: str,
        embedder_version: str,
        embedding_params_hash: str,
        embedding_run_id: str,
    ) -> dict[str, Any]:
        return {
            "source_type": source_type,
            "timestamp": timestamp,
            "security_clearance": security_clearance,
            "doc_id": doc_id,
            "source_key": source_key,
            "chunk_index": chunk_index,
            "chunk_text": text,
            "run_id": run_id,
            "embedder_name": embedder_name,
            "embedder_version": embedder_version,
            "embedding_params_hash": embedding_params_hash,
            "embedding_run_id": embedding_run_id,
        }

    def _embedding_object_key(self, doc_id: str, chunk_id: str) -> str:
        return f"{self.output_prefix}{doc_id}/{chunk_id}.embedding.json"

    @staticmethod
    def _doc_id_from_destination_key(destination_key: str) -> str:
        parts = [part for part in destination_key.split("/") if part]
        try:
            chunks_index = parts.index("chunks")
            return parts[chunks_index + 1]
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Could not extract doc_id from chunk destination key: {destination_key}") from exc
