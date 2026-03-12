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
    source_uri: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, source_uri: str) -> "ChunkArtifactPayload":
        return cls(
            chunk_record=ChunkRecordPayload(**dict(payload)),
            source_uri=source_uri,
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
        self._dimension = dimension
        self._storage_gateway = object_storage
        self._storage_bucket = storage_bucket
        self._output_prefix = output_prefix

    @staticmethod
    def _deterministic_embedding_for(text: str, dimension: int) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(dimension):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values

    @staticmethod
    def read_chunk_payload(raw_payload: bytes, *, source_uri: str) -> ChunkArtifactPayload:
        payload = dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))
        return ChunkArtifactPayload.from_dict(payload, source_uri=source_uri)

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
        destination_uri = self._storage_gateway.build_uri(self._storage_bucket, destination_key)
        if self._storage_gateway.object_exists(self._storage_bucket, destination_key):
            return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=False)
        self._storage_gateway.write_object(
            uri=destination_uri,
            payload=json.dumps(embedding_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
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
        doc_id = self._doc_id_from_source_uri(payload.source_uri)
        chunk_id = payload.chunk_record.chunk_id
        embedder_params = {"dimension": int(self._dimension)}
        return {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": self._deterministic_embedding_for(text, self._dimension),
            "metadata": self._metadata_from_payload(
                source_type=None,
                timestamp=None,
                security_clearance=None,
                doc_id=doc_id,
                source_uri=payload.source_uri,
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
        source_uri: Any,
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
            "source_uri": source_uri,
            "chunk_index": chunk_index,
            "chunk_text": text,
            "run_id": run_id,
            "embedder_name": embedder_name,
            "embedder_version": embedder_version,
            "embedding_params_hash": embedding_params_hash,
            "embedding_run_id": embedding_run_id,
        }

    def _embedding_object_key(self, doc_id: str, chunk_id: str) -> str:
        return f"{self._output_prefix}{doc_id}/{chunk_id}.embedding.json"

    def output_uri(self, destination_key: str) -> str:
        """Build the storage URI for a written embedding artifact."""
        return self._storage_gateway.build_uri(self._storage_bucket, destination_key)

    @staticmethod
    def _doc_id_from_source_uri(source_uri: str) -> str:
        uri_without_scheme = source_uri.split("://", maxsplit=1)[-1]
        key = uri_without_scheme.split("/", maxsplit=1)[1]
        parts = [part for part in key.split("/") if part]
        if not parts:
            raise ValueError(f"Could not extract doc_id from chunk source uri: {source_uri}")
        return parts[0]
