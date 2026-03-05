import logging
import json
from typing import Any
from datetime import UTC, datetime

from contracts.contracts import IndexWeaviateProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.processing_engine import ReadGateway, WriteGateway
from pipeline_common.provenance import (
    EmbeddingRegistryRow,
    EmbeddingRegistryStatus,
    ProvenanceRegistryGateway,
    build_embedding_envelope,
    sha256_hex,
)
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, StageQueue
from pipeline_common.helpers.contracts import utc_now_iso
from services.weaviate_gateway import upsert_chunk, verify_query
from pipeline_common.startup.contracts import WorkerService
from services.index_weaviate_processor import IndexWeaviateProcessor

logger = logging.getLogger(__name__)


class WorkerIndexWeaviateService(WorkerService):
    """Index embeddings artifacts into Weaviate and persist status objects."""

    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        provenance_registry: ProvenanceRegistryGateway,
        spark_session: Any | None,
        processing_config: IndexWeaviateProcessingConfigContract,
        weaviate_url: str,
    ) -> None:
        """Initialize indexing worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.provenance_registry = provenance_registry
        self.spark_session = spark_session
        self.read_gateway = ReadGateway(spark_session=self.spark_session) if self.spark_session is not None else None
        self.write_gateway = WriteGateway() if self.spark_session is not None else None
        self.weaviate_url = weaviate_url
        self.index_target = "weaviate://DocumentChunk"
        self._initialize_runtime_config(processing_config)
        self.processor = IndexWeaviateProcessor(
            output_prefix=self.output_prefix,
            spark_session=self.spark_session,
        )

    def serve(self) -> None:
        """Run the indexing worker loop by polling queue messages."""
        while True:
            message = self.stage_queue.pop_message()
            if message is None:
                continue
            try:
                request = self._request_from_message(message)
            except Exception:
                message.nack(requeue=True)
                logger.exception("Failed index invalid-message handling; requeued message")
                continue
            if request is None:
                continue
            embeddings_key, doc_id = request
            try:
                self._handle_index_request(embeddings_key, doc_id)
            except Exception:
                if self._handle_index_failure(embeddings_key, doc_id):
                    message.ack()
                else:
                    message.nack(requeue=True)
                continue
            message.ack()

    def _handle_index_request(self, embeddings_key: str, doc_id: str) -> None:
        index_job = self._build_index_job(embeddings_key, doc_id)
        if index_job is None:
            return

        self.lineage.start_run()
        self.lineage.add_input(
            name=f"{self.storage_bucket}/{index_job['embeddings_key']}",
            platform=DatasetPlatform.S3,
        )
        try:
            payload = self._read_embeddings_payload(index_job["embeddings_key"])
            resolved_doc_id = str(payload.get("doc_id", index_job["doc_id"]))
            resolved_chunk_id = str(payload.get("chunk_id", ""))
            destination_key = self.processor.build_indexed_key(resolved_doc_id, resolved_chunk_id)
            self.lineage.add_output(
                name=f"{self.storage_bucket}/{destination_key}",
                platform=DatasetPlatform.S3,
            )
            self.lineage.add_output(
                name=f"{self.storage_bucket}/07_metadata/provenance/embedding/latest/",
                platform=DatasetPlatform.S3,
            )
            if self.object_storage.object_exists(self.storage_bucket, destination_key):
                self._send_index_failure(index_job["embeddings_key"], resolved_doc_id)
                self.lineage.fail_run(error_message=f"Index status already exists: {destination_key}")
                return

            self._upsert_embeddings(payload)
            self._write_indexed_object(destination_key, resolved_doc_id, resolved_chunk_id)
            self.lineage.complete_run()
            logger.info("Wrote indexed status '%s'", destination_key)
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            raise

    def _send_index_failure(self, embeddings_key: str, doc_id: str) -> None:
        self.stage_queue.push_dlq(
            Envelope(
                type="index_weaviate.failure",
                payload={"embeddings_key": embeddings_key, "doc_id": doc_id},
            ).to_dict()
        )

    def _handle_index_failure(self, embeddings_key: str, doc_id: str) -> bool:
        """Route failed index request to DLQ; return True when message can be acked."""
        try:
            self._send_index_failure(embeddings_key, doc_id)
        except Exception:
            logger.exception(
                "Failed indexing embeddings key '%s' and failed DLQ publish; requeueing message",
                embeddings_key,
            )
            return False
        logger.exception("Failed indexing embeddings key '%s'; sent to DLQ", embeddings_key)
        return True

    def _build_index_job(self, embeddings_key: str, doc_id: str) -> dict[str, str] | None:
        if not embeddings_key.startswith(self.input_prefix) or embeddings_key == self.input_prefix:
            return None
        if not embeddings_key.endswith(self.embeddings_suffix):
            return None
        return {"embeddings_key": embeddings_key, "doc_id": doc_id}

    def _read_embeddings_payload(self, embeddings_key: str) -> dict[str, Any]:
        raw_payload = self.object_storage.read_object(self.storage_bucket, embeddings_key)
        return self.processor.read_embeddings_payload(raw_payload)

    def _upsert_embeddings(self, payload: dict[str, Any]) -> None:
        if self.spark_session is None:
            items = self.processor.build_upsert_items(payload)
        else:
            input_records = self.processor.build_input_records(payload)
            input_df = self.read_gateway.from_records(input_records)
            items = self.processor.build_upsert_items_from_dataframe(
                input_df,
                write_gateway=self.write_gateway,
            )
        for item in items:
            properties = dict(item.get("properties", {}))
            vector = list(item.get("vector", []))
            chunk_id = str(item["chunk_id"])
            envelope = build_embedding_envelope(
                chunk_id=chunk_id,
                index_target=self.index_target,
                embedder_name=str(properties.get("embedder_name", "unknown_embedder")),
                embedder_version=str(properties.get("embedder_version", "unknown_version")),
                embedder_params={"embedding_params_hash": str(properties.get("embedding_params_hash", ""))},
                embedding_params_hash_value=str(properties.get("embedding_params_hash", "")) or None,
                embedding_dim=len(vector),
                embedding_run_id=str(properties.get("embedding_run_id", "")),
                chunking_run_id=str(properties.get("chunking_run_id", "")),
                vector=vector,
                vector_record_id=chunk_id,
            )
            properties.update(
                {
                    "embedding_id": str(envelope["embedding_id"]),
                    "index_target": self.index_target,
                    "embedding_run_id": str(envelope["embedding_run_id"]),
                    "chunking_run_id": str(envelope["chunking_run_id"]),
                    "embedder_name": str(envelope["embedder_name"]),
                    "embedder_version": str(envelope["embedder_version"]),
                    "embedding_params_hash": str(envelope["embedding_params_hash"]),
                }
            )
            upsert_chunk(
                self.weaviate_url,
                chunk_id=chunk_id,
                vector=vector,
                properties=properties,
            )
            now_iso = datetime.now(tz=UTC).isoformat()
            self.provenance_registry.upsert_embedding_succeeded(
                EmbeddingRegistryRow(
                    embedding_id=str(envelope["embedding_id"]),
                    chunk_id=chunk_id,
                    index_target=self.index_target,
                    embedder_name=str(envelope["embedder_name"]),
                    embedder_version=str(envelope["embedder_version"]),
                    embedding_params_hash=str(envelope["embedding_params_hash"]),
                    embedding_dim=int(envelope["embedding_dim"]),
                    embedding_vector_hash=sha256_hex(str(vector)),
                    embedding_run_id=str(envelope["embedding_run_id"]),
                    chunking_run_id=str(envelope["chunking_run_id"]),
                    attempt=1,
                    status=EmbeddingRegistryStatus.SUCCEEDED,
                    error_message=None,
                    started_at=now_iso,
                    finished_at=now_iso,
                    upserted_at=now_iso,
                    vector_record_id=chunk_id,
                )
            )

    def _write_indexed_object(self, destination_key: str, doc_id: str, chunk_id: str) -> None:
        status_payload = self.processor.build_index_status_payload(doc_id, chunk_id)
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(status_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )
        result = verify_query(self.weaviate_url, "logistics")
        logger.info("Indexed doc_id '%s' verify=%s", doc_id, bool(result))

    def _request_from_message(self, message: ConsumedMessage) -> tuple[str, str] | None:
        """Parse index request from queue payload; route invalid payloads to DLQ."""
        try:
            envelope = Envelope.from_dict(message.payload)
            return str(envelope.payload["embeddings_key"]), str(envelope.payload["doc_id"])
        except Exception as exc:
            self.stage_queue.push_dlq(
                Envelope(
                    type="index_weaviate.invalid_message",
                    payload={
                        "error": str(exc),
                        "message_payload": message.payload,
                        "failed_at": utc_now_iso(),
                    },
                ).to_dict()
            )
            message.ack()
            logger.exception("Invalid index queue message payload; sent to DLQ and acknowledged")
            return None

    def _initialize_runtime_config(self, processing_config: IndexWeaviateProcessingConfigContract) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.input_prefix = processing_config.storage.input_prefix
        self.output_prefix = processing_config.storage.output_prefix
        self.embeddings_suffix = ".embedding.json"
