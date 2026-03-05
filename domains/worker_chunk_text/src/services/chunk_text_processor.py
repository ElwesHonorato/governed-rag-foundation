import json
import tempfile
from pathlib import Path
from typing import Any

from chunking.domain.text_chunker import chunk_text
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.processing_engine import SparkWriteGateway
from pipeline_common.helpers.contracts import chunk_id_for
from pyspark.sql import functions as spark_functions  # type: ignore
from pyspark.sql import types as spark_types  # type: ignore


class ChunkTextProcessor:
    """Transform processed payloads into chunk artifacts and write outputs."""

    def __init__(
        self,
        *,
        spark_session: Any | None,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        self.spark_session = spark_session
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix

    @staticmethod
    def read_processed_payload(raw_payload: bytes) -> dict[str, Any]:
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def write_chunk_artifacts(self, processed: dict[str, Any], *, doc_id: str) -> tuple[int, list[str]]:
        """Build chunk rows with local Python path and write chunk objects."""
        records = self._build_chunk_records_local(processed, doc_id)
        return self._write_chunk_records(records)

    def build_input_record(self, processed: dict[str, Any], *, doc_id: str) -> dict[str, Any]:
        """Create one normalized record for Spark dataframe input."""
        parsed_payload = processed.get("parsed")
        parsed_text = parsed_payload.get("text", "") if isinstance(parsed_payload, dict) else ""
        source_text = str(parsed_text or processed.get("text", ""))
        return {
            "doc_id": doc_id,
            "source_text": source_text,
            "source_type": processed.get("source_type", "html"),
            "timestamp": processed.get("timestamp"),
            "security_clearance": processed.get("security_clearance", "internal"),
            "source_key": processed.get("source_key"),
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
            destination_key = self._chunk_object_key(doc_id, str(chunk_record["chunk_id"]))
            destination_keys.append(destination_key)
            if self.object_storage.object_exists(self.storage_bucket, destination_key):
                continue
            self.object_storage.write_object(
                self.storage_bucket,
                destination_key,
                json.dumps(chunk_record, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
                content_type="application/json",
            )
            written += 1
        return written, destination_keys

    @staticmethod
    def _build_chunk_records_local(processed: dict[str, Any], doc_id: str) -> list[dict[str, Any]]:
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

    @staticmethod
    def _build_chunk_dataframe(input_df: Any) -> Any:
        chunker_udf = spark_functions.udf(
            lambda text: chunk_text(str(text)),
            spark_types.ArrayType(spark_types.StringType()),
        )
        return (
            input_df.withColumn("chunk_texts", chunker_udf(spark_functions.col("source_text")))
            .select(
                "doc_id",
                "source_type",
                "timestamp",
                "security_clearance",
                "source_key",
                spark_functions.posexplode(spark_functions.col("chunk_texts")).alias("chunk_index", "chunk_text"),
            )
            .drop("source_text")
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
                    index = int(row["chunk_index"])
                    records.append(
                        {
                            "chunk_id": chunk_id_for(doc_id, index, chunk_text_value),
                            "doc_id": doc_id,
                            "chunk_index": index,
                            "chunk_text": chunk_text_value,
                            "source_type": row.get("source_type"),
                            "timestamp": row.get("timestamp"),
                            "security_clearance": row.get("security_clearance"),
                            "source_key": row.get("source_key"),
                        }
                    )
        return records

    def _chunk_object_key(self, doc_id: str, chunk_id: str) -> str:
        return f"{self.output_prefix}{doc_id}/{chunk_id}.chunk.json"
