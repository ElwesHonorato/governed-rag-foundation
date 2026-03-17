"""Embedding processor implementation for worker_embed_chunks."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.helpers.run_ids import build_source_run_id
from pipeline_common.provenance import embedding_params_hash
from pipeline_common.stages_contracts import (
    EmbeddingArtifact,
    EmbeddingArtifactMetadata,
    FileMetadata,
    ProcessResult,
    ProcessorContext,
    StageArtifact,
)
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata

EMBEDDER_NAME = "deterministic_sha256"
EMBEDDER_VERSION = "1.0.0"


@dataclass(frozen=True)
class EmbeddingWriteResult:
    """Result of attempting to write one embedding artifact."""

    destination_key: str
    doc_id: str
    chunk_id: str
    wrote: bool


@dataclass(frozen=True)
class ChunkRecordPayload:
    """Chunk fields required to derive an embedding artifact."""

    index: int
    chunk_id: str
    offsets_start: int
    offsets_end: int
    chunk_text_hash: str


@dataclass(frozen=True)
class ChunkArtifactPayload:
    """Chunk artifact fields used to derive an embedding artifact."""

    chunk_record: ChunkRecordPayload
    chunk_text: str
    root_doc_metadata: FileMetadata
    source_uri: str

    @classmethod
    def from_stage_artifact(cls, artifact: StageArtifact, *, source_uri: str) -> "ChunkArtifactPayload":
        """Build the embedding input payload from a stored chunk artifact."""
        chunk_record_payload = dict(artifact.content_metadata)
        return cls(
            chunk_record=ChunkRecordPayload(**chunk_record_payload),
            chunk_text=str(artifact.content.data),
            root_doc_metadata=artifact.root_doc_metadata,
            source_uri=source_uri,
        )


class EmbedChunksProcessor:
    """Build embedding payloads from chunk payloads and write outputs."""

    def __init__(
        self,
        *,
        embedder: DeterministicHashEmbedder,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        """Initialize embedding processor dependencies."""
        self._embedder = embedder
        self._storage_gateway = object_storage
        self._storage_bucket = storage_bucket
        self._output_prefix = output_prefix

    @staticmethod
    def read_chunk_payload(raw_payload: bytes, *, source_uri: str) -> ChunkArtifactPayload:
        """Parse one stored chunk artifact payload."""
        payload = dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))
        artifact = StageArtifact.from_dict(payload)
        return ChunkArtifactPayload.from_stage_artifact(artifact, source_uri=source_uri)

    def process(
        self,
        *,
        input_uri: str,
        raw_payload: bytes,
    ) -> ProcessResult:
        """Build one embedding artifact and return the process result."""
        chunk_payload = self.read_chunk_payload(raw_payload, source_uri=input_uri)
        run_id = build_source_run_id(input_uri)
        stage_doc_metadata = FileMetadata.from_source_bytes(
            uri=input_uri,
            payload=raw_payload,
            default_content_type="application/json",
        )
        write_result = self.write_embedding_artifact(
            chunk_payload,
            run_id=run_id,
            embedding_run_id=self._embedding_run_id(),
            stage_doc_metadata=stage_doc_metadata,
        )
        return ProcessResult(
            run_id=run_id,
            root_doc_metadata=chunk_payload.root_doc_metadata,
            stage_doc_metadata=stage_doc_metadata,
            input_uri=input_uri,
            processor_context=ProcessorContext(params_hash="", params=[]),
            processor=ProcessorMetadata(name="EmbedChunksProcessor", version="1.0.0"),
            result={
                "destination_key": write_result.destination_key,
                "output_uri": self.output_uri(write_result.destination_key),
            },
        )

    def write_embedding_artifact(
        self,
        payload: ChunkArtifactPayload,
        *,
        run_id: str,
        embedding_run_id: str,
        stage_doc_metadata: FileMetadata,
    ) -> EmbeddingWriteResult:
        """Write one embedding artifact for the provided chunk payload."""
        embedding_payload = self._build_embedding_payload(
            payload,
            run_id=run_id,
            embedding_run_id=embedding_run_id,
            stage_doc_metadata=stage_doc_metadata,
        )
        return self._write_embedding_payload(embedding_payload)

    def _write_embedding_payload(self, embedding_artifact: EmbeddingArtifact) -> EmbeddingWriteResult:
        """Persist one embedding payload if it does not already exist."""
        doc_id = embedding_artifact.doc_id
        chunk_id = embedding_artifact.chunk_id
        destination_key = self._embedding_object_key(doc_id, chunk_id)
        destination_uri = self._storage_gateway.build_uri(self._storage_bucket, destination_key)
        if self._storage_gateway.object_exists(self._storage_bucket, destination_key):
            return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=False)
        self._storage_gateway.write_object(
            uri=destination_uri,
            payload=json.dumps(
                embedding_artifact.to_dict,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )
        return EmbeddingWriteResult(destination_key=destination_key, doc_id=doc_id, chunk_id=chunk_id, wrote=True)

    def _build_embedding_payload(
        self,
        payload: ChunkArtifactPayload,
        *,
        run_id: str,
        embedding_run_id: str,
        stage_doc_metadata: FileMetadata,
    ) -> EmbeddingArtifact:
        """Build the storage payload for one embedding artifact."""
        text = payload.chunk_text
        doc_id = payload.root_doc_metadata.doc_id
        chunk_id = payload.chunk_record.chunk_id
        embedder_params = {"dimension": int(self._embedder.dimensions)}
        return EmbeddingArtifact(
            doc_id=doc_id,
            chunk_id=chunk_id,
            chunk_text=text,
            vector=self._embedder.embed(text),
            metadata=EmbeddingArtifactMetadata(
                run_id=run_id,
                embedder_name=EMBEDDER_NAME,
                embedder_version=EMBEDDER_VERSION,
                embedding_params_hash=embedding_params_hash(embedder_params),
                embedding_run_id=embedding_run_id,
                root_doc_metadata=payload.root_doc_metadata,
                stage_doc_metadata=stage_doc_metadata,
            ),
        )

    def _embedding_object_key(self, doc_id: str, chunk_id: str) -> str:
        return f"{self._output_prefix}{doc_id}/{chunk_id}.embedding.json"

    def output_uri(self, destination_key: str) -> str:
        """Build the storage URI for a written embedding artifact."""
        return self._storage_gateway.build_uri(self._storage_bucket, destination_key)

    @staticmethod
    def _embedding_run_id() -> str:
        """Build a unique run identifier for one embedding write."""
        return uuid.uuid4().hex
