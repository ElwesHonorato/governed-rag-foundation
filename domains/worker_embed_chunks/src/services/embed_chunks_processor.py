import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.processing_engine import SparkWriteGateway
from pipeline_common.provenance import embedding_params_hash
from pipeline_common.stages_contracts import ChunkArtifactPayload
from pyspark.sql import functions as spark_functions  # type: ignore
from pyspark.sql import types as spark_types  # type: ignore

EMBEDDER_NAME = "deterministic_sha256"
EMBEDDER_VERSION = "1.0.0"


@dataclass(frozen=True)
class EmbeddingWriteResult:
    destination_key: str
    doc_id: str
    chunk_id: str
    wrote: bool


class EmbedChunksProcessor:
    """Build embedding payloads from chunk payloads and write outputs."""

    def __init__(
        self,
        *,
        dimension: int,
        spark_session: Any | None,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        self.dimension = dimension
        self.spark_session = spark_session
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
    def read_chunk_payload(raw_payload: bytes) -> ChunkArtifactPayload:
        payload = dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))
        return ChunkArtifactPayload.from_dict(payload)

    def write_embedding_artifact(
        self,
        payload: ChunkArtifactPayload,
        *,
        embedding_run_id: str,
    ) -> EmbeddingWriteResult:
        embedding_payload = self._build_embedding_payload_local(payload, embedding_run_id=embedding_run_id)
        return self._write_embedding_payload(embedding_payload)

    def build_input_record(self, payload: ChunkArtifactPayload, *, embedding_run_id: str) -> dict[str, Any]:
        """Create one normalized record for Spark dataframe input."""
        text = payload.chunk_text
        source_metadata = payload.source_metadata
        provenance = payload.provenance
        embedder_params = {"dimension": int(self.dimension)}
        return {
            "doc_id": source_metadata.doc_id,
            "chunk_id": provenance.chunk_id,
            "chunk_text": text,
            "source_type": source_metadata.source_type,
            "timestamp": source_metadata.timestamp,
            "security_clearance": source_metadata.security_clearance,
            "source_key": source_metadata.source_key,
            "chunk_index": payload.chunk_index,
            "dimension": int(self.dimension),
            "run_id": provenance.run_id,
            "embedder_name": EMBEDDER_NAME,
            "embedder_version": EMBEDDER_VERSION,
            "embedding_params_hash": embedding_params_hash(embedder_params),
            "embedding_run_id": embedding_run_id,
        }

    def write_embedding_artifact_from_dataframe(
        self,
        input_df: Any,
        *,
        write_gateway: SparkWriteGateway,
    ) -> EmbeddingWriteResult:
        """Transform dataframe and materialize embedding payload via write gateway."""
        transformed_df = self._build_embedding_dataframe(input_df)
        record = self._materialize_first_record(transformed_df, write_gateway=write_gateway)
        embedding_payload = self._build_embedding_payload_from_record(record)
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
        text = payload.chunk_text
        doc_id = payload.source_metadata.doc_id
        chunk_id = payload.provenance.chunk_id
        embedder_params = {"dimension": int(self.dimension)}
        return {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": self._deterministic_embedding_for(text, self.dimension),
            "metadata": self._metadata_from_payload(
                source_type=payload.source_metadata.source_type,
                timestamp=payload.source_metadata.timestamp,
                security_clearance=payload.source_metadata.security_clearance,
                doc_id=doc_id,
                source_key=payload.source_metadata.source_key,
                chunk_index=payload.chunk_index,
                text=text,
                run_id=payload.provenance.run_id,
                embedder_name=EMBEDDER_NAME,
                embedder_version=EMBEDDER_VERSION,
                embedding_params_hash=embedding_params_hash(embedder_params),
                embedding_run_id=embedding_run_id,
            ),
        }

    def _build_embedding_dataframe(self, input_df: Any) -> Any:
        vector_udf = spark_functions.udf(
            lambda value, dim: self._deterministic_embedding_for(str(value), int(dim)),
            spark_types.ArrayType(spark_types.DoubleType()),
        )
        return input_df.withColumn(
            "vector",
            vector_udf(spark_functions.col("chunk_text"), spark_functions.col("dimension")),
        )

    def _materialize_first_record(
        self,
        dataframe: Any,
        *,
        write_gateway: SparkWriteGateway,
    ) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="worker_embed_chunks_") as temp_dir:
            write_gateway.write(
                dataframe,
                path=temp_dir,
                format_name="json",
                mode="overwrite",
            )
            json_parts = sorted(Path(temp_dir).glob("part-*"))
            for part in json_parts:
                with part.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        return dict(json.loads(line))
        raise RuntimeError("No records produced by Spark embedding transform")

    def _build_embedding_payload_from_record(self, row: dict[str, Any]) -> dict[str, Any]:
        doc_id = str(row["doc_id"])
        chunk_id = str(row["chunk_id"])
        text = str(row["chunk_text"])
        return {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": list(row.get("vector", [])),
            "metadata": self._metadata_from_payload(
                source_type=row.get("source_type"),
                timestamp=row.get("timestamp"),
                security_clearance=row.get("security_clearance"),
                doc_id=doc_id,
                source_key=row.get("source_key"),
                chunk_index=row.get("chunk_index"),
                text=text,
                run_id=str(row.get("run_id", "")),
                embedder_name=str(row.get("embedder_name", EMBEDDER_NAME)),
                embedder_version=str(row.get("embedder_version", EMBEDDER_VERSION)),
                embedding_params_hash=str(row.get("embedding_params_hash", "")),
                embedding_run_id=str(row.get("embedding_run_id", "")),
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
