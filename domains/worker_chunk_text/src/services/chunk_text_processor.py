import json
import tempfile
from pathlib import Path
from typing import Any

from chunking.domain.text_chunker import chunk_text
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.processing_engine import SparkWriteGateway
from pipeline_common.provenance import (
    ChunkRegistryRow,
    ChunkRegistryStatus,
    ProvenanceRegistryGateway,
    build_chunk_envelope,
    source_content_hash,
)
from pipeline_common.helpers.contracts import utc_now_iso
from pyspark.sql import functions as spark_functions  # type: ignore
from pyspark.sql import types as spark_types  # type: ignore

CHUNKER_NAME = "text_chunker"
CHUNKER_VERSION = "1.0.0"
CHUNKER_PARAMS = {"strategy": "default"}


class ChunkTextProcessor:
    """Transform processed payloads into chunk artifacts and write outputs."""

    def __init__(
        self,
        *,
        spark_session: Any | None,
        object_storage: ObjectStorageGateway,
        provenance_registry: ProvenanceRegistryGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        self.spark_session = spark_session
        self.object_storage = object_storage
        self.provenance_registry = provenance_registry
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix

    @staticmethod
    def read_processed_payload(raw_payload: bytes) -> dict[str, Any]:
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def write_chunk_artifacts(
        self,
        processed: dict[str, Any],
        *,
        doc_id: str,
        chunking_run_id: str,
    ) -> tuple[int, list[str]]:
        """Build chunk rows with local Python path and write chunk objects."""
        records = self._build_chunk_records_local(processed, doc_id, chunking_run_id=chunking_run_id)
        return self._write_chunk_records(records)

    def build_input_record(self, processed: dict[str, Any], *, doc_id: str, chunking_run_id: str) -> dict[str, Any]:
        """Create one normalized record for Spark dataframe input."""
        parsed_payload = processed.get("parsed")
        parsed_text = parsed_payload.get("text", "") if isinstance(parsed_payload, dict) else ""
        source_text = str(parsed_text or processed.get("text", ""))
        source_key = str(processed.get("source_key", ""))
        source_dataset_urn = f"s3://{self.storage_bucket}/{source_key}"
        return {
            "doc_id": doc_id,
            "source_text": source_text,
            "source_type": processed.get("source_type", "html"),
            "timestamp": processed.get("timestamp"),
            "security_clearance": processed.get("security_clearance", "internal"),
            "source_key": source_key,
            "source_dataset_urn": source_dataset_urn,
            "source_content_hash": source_content_hash(source_text.encode("utf-8")),
            "chunking_run_id": chunking_run_id,
        }

    def write_chunk_artifacts_from_dataframe(
        self,
        input_df: Any,
        *,
        write_gateway: SparkWriteGateway,
    ) -> tuple[int, list[str]]:
        """Transform input dataframe and materialize chunk artifacts via write gateway."""
        transformed_df = self._build_chunk_dataframe(input_df)
        records = self._materialize_records_from_dataframe(transformed_df, write_gateway=write_gateway)
        return self._write_chunk_records(records)

    def _write_chunk_records(self, records: list[dict[str, Any]]) -> tuple[int, list[str]]:
        written = 0
        destination_keys: list[str] = []
        for chunk_record in records:
            doc_id = str(chunk_record["doc_id"])
            source_s3_uri = str(chunk_record["source_s3_uri"])
            envelope = build_chunk_envelope(
                source_dataset_urn=str(chunk_record["source_dataset_urn"]),
                source_s3_uri=source_s3_uri,
                source_content_hash=str(chunk_record["source_content_hash"]),
                chunk_s3_uri="pending",
                chunk_text=str(chunk_record["chunk_text"]),
                offsets_start=int(chunk_record["offsets_start"]),
                offsets_end=int(chunk_record["offsets_end"]),
                chunker_name=CHUNKER_NAME,
                chunker_version=CHUNKER_VERSION,
                chunker_params=CHUNKER_PARAMS,
                chunking_run_id=str(chunk_record["chunking_run_id"]),
                breadcrumb=chunk_record.get("breadcrumb"),
            )
            destination_key = self._chunk_object_key(doc_id, str(envelope["chunk_id"]))
            chunk_s3_uri = f"s3://{self.storage_bucket}/{destination_key}"
            envelope["chunk_s3_uri"] = chunk_s3_uri
            destination_keys.append(destination_key)
            artifact_payload = dict(chunk_record)
            artifact_payload["chunk_id"] = envelope["chunk_id"]
            artifact_payload["provenance"] = envelope
            if not self.object_storage.object_exists(self.storage_bucket, destination_key):
                self.object_storage.write_object(
                    self.storage_bucket,
                    destination_key,
                    json.dumps(artifact_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
                        "utf-8"
                    ),
                    content_type="application/json",
                )
                written += 1
            self.provenance_registry.upsert_chunk(
                ChunkRegistryRow(
                    chunk_id=str(envelope["chunk_id"]),
                    source_dataset_urn=str(envelope["source_dataset_urn"]),
                    source_s3_uri=str(envelope["source_s3_uri"]),
                    source_content_hash=str(envelope["source_content_hash"]),
                    chunk_s3_uri=str(envelope["chunk_s3_uri"]),
                    offsets_start=int(envelope["offsets_start"]),
                    offsets_end=int(envelope["offsets_end"]),
                    breadcrumb=str(envelope["breadcrumb"]) if envelope.get("breadcrumb") else None,
                    chunk_text_hash=str(envelope["chunk_text_hash"]),
                    chunker_name=str(envelope["chunker_name"]),
                    chunker_version=str(envelope["chunker_version"]),
                    chunk_params_hash=str(envelope["chunk_params_hash"]),
                    chunking_run_id=str(envelope["chunking_run_id"]),
                    created_at=utc_now_iso(),
                    observed_at=utc_now_iso(),
                    status=ChunkRegistryStatus.ACTIVE,
                )
            )
        return written, destination_keys

    def _build_chunk_records_local(
        self,
        processed: dict[str, Any],
        doc_id: str,
        *,
        chunking_run_id: str,
    ) -> list[dict[str, Any]]:
        parsed_payload = processed.get("parsed")
        parsed_text = parsed_payload.get("text", "") if isinstance(parsed_payload, dict) else ""
        source_text = str(parsed_text or processed.get("text", ""))
        source_key = str(processed.get("source_key", ""))
        source_dataset_urn = f"s3://{self.storage_bucket}/{source_key}"
        source_hash = source_content_hash(source_text.encode("utf-8"))
        source_segments = self._chunk_segments(source_text)
        records: list[dict[str, Any]] = []
        for chunk_index, chunk_value, start, end in source_segments:
            records.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": "pending",
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_value,
                    "source_type": processed.get("source_type", "html"),
                    "timestamp": processed.get("timestamp"),
                    "security_clearance": processed.get("security_clearance", "internal"),
                    "source_key": source_key,
                    "source_dataset_urn": source_dataset_urn,
                    "source_s3_uri": source_dataset_urn,
                    "source_content_hash": source_hash,
                    "offsets_start": start,
                    "offsets_end": end,
                    "breadcrumb": f"chunk[{chunk_index}]",
                    "chunking_run_id": chunking_run_id,
                }
            )
        return records

    @staticmethod
    def _chunk_segments(source_text: str) -> list[tuple[int, str, int, int]]:
        chunks = chunk_text(source_text)
        cursor = 0
        segments: list[tuple[int, str, int, int]] = []
        for index, chunk_value in enumerate(chunks):
            resolved = source_text.find(chunk_value, cursor)
            start = resolved if resolved >= 0 else cursor
            end = start + len(chunk_value)
            segments.append((index, chunk_value, start, end))
            cursor = end
        return segments

    @staticmethod
    def _build_chunk_dataframe(input_df: Any) -> Any:
        chunk_struct_type = spark_types.StructType(
            [
                spark_types.StructField("chunk_index", spark_types.IntegerType(), nullable=False),
                spark_types.StructField("chunk_text", spark_types.StringType(), nullable=False),
                spark_types.StructField("offsets_start", spark_types.IntegerType(), nullable=False),
                spark_types.StructField("offsets_end", spark_types.IntegerType(), nullable=False),
            ]
        )
        chunker_udf = spark_functions.udf(
            lambda text: [
                {
                    "chunk_index": index,
                    "chunk_text": value,
                    "offsets_start": start,
                    "offsets_end": end,
                }
                for index, value, start, end in ChunkTextProcessor._chunk_segments(str(text))
            ],
            spark_types.ArrayType(chunk_struct_type),
        )
        return (
            input_df.withColumn("chunk_structs", chunker_udf(spark_functions.col("source_text")))
            .withColumn("chunk_struct", spark_functions.explode(spark_functions.col("chunk_structs")))
            .select(
                "doc_id",
                "source_type",
                "timestamp",
                "security_clearance",
                "source_key",
                "source_dataset_urn",
                "source_content_hash",
                "chunking_run_id",
                spark_functions.col("chunk_struct.chunk_index").alias("chunk_index"),
                spark_functions.col("chunk_struct.chunk_text").alias("chunk_text"),
                spark_functions.col("chunk_struct.offsets_start").alias("offsets_start"),
                spark_functions.col("chunk_struct.offsets_end").alias("offsets_end"),
            )
        )

    def _materialize_records_from_dataframe(
        self,
        dataframe: Any,
        *,
        write_gateway: SparkWriteGateway,
    ) -> list[dict[str, Any]]:
        with tempfile.TemporaryDirectory(prefix="worker_chunk_text_") as temp_dir:
            write_gateway.write(
                dataframe,
                path=temp_dir,
                format_name="json",
                mode="overwrite",
            )
            json_parts = sorted(Path(temp_dir).glob("part-*"))
            return self._read_json_parts_as_records(json_parts)

    @staticmethod
    def _read_json_parts_as_records(json_parts: list[Path]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for part in json_parts:
            with part.open("r", encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    doc_id = str(row["doc_id"])
                    chunk_text_value = str(row["chunk_text"])
                    chunk_index = int(row["chunk_index"])
                    records.append(
                        {
                            "doc_id": doc_id,
                            "chunk_id": "pending",
                            "chunk_index": chunk_index,
                            "chunk_text": chunk_text_value,
                            "source_type": row.get("source_type"),
                            "timestamp": row.get("timestamp"),
                            "security_clearance": row.get("security_clearance"),
                            "source_key": row.get("source_key"),
                            "source_dataset_urn": row.get("source_dataset_urn"),
                            "source_s3_uri": row.get("source_dataset_urn"),
                            "source_content_hash": row.get("source_content_hash"),
                            "offsets_start": int(row["offsets_start"]),
                            "offsets_end": int(row["offsets_end"]),
                            "breadcrumb": f"chunk[{chunk_index}]",
                            "chunking_run_id": row.get("chunking_run_id"),
                        }
                    )
        return records

    def _chunk_object_key(self, doc_id: str, chunk_id: str) -> str:
        return f"{self.output_prefix}{doc_id}/{chunk_id}.chunk.json"
