import logging
import json
from typing import Any

from contracts.contracts import IndexWeaviateProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import Envelope, StageQueue
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
        spark_session: Any | None,
        processing_config: IndexWeaviateProcessingConfigContract,
        weaviate_url: str,
    ) -> None:
        """Initialize indexing worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.spark_session = spark_session
        self.weaviate_url = weaviate_url
        self._initialize_runtime_config(processing_config)
        self.processor = IndexWeaviateProcessor(
            output_prefix=self.output_prefix,
            spark_session=self.spark_session,
        )

    def serve(self) -> None:
        """Run the indexing worker loop by polling queue messages."""
        while True:
            request = self._pop_queued_request()
            if request is None:
                continue
            embeddings_key, doc_id = request
            try:
                self._handle_index_request(embeddings_key, doc_id)
            except Exception:
                self._send_index_failure(embeddings_key, doc_id)
                logger.exception("Failed indexing embeddings key '%s'; sent to DLQ", embeddings_key)

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
        items = self.processor.build_upsert_items(payload)
        for item in items:
            upsert_chunk(
                self.weaviate_url,
                chunk_id=str(item["chunk_id"]),
                vector=item.get("vector", []),
                properties=dict(item.get("properties", {})),
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

    def _pop_queued_request(self) -> tuple[str, str] | None:
        """Pop one indexing request from queue when available."""
        raw = self.stage_queue.pop_message()
        if raw is None:
            return None
        envelope = Envelope.from_dict(raw)
        return str(envelope.payload["embeddings_key"]), str(envelope.payload["doc_id"])

    def _initialize_runtime_config(self, processing_config: IndexWeaviateProcessingConfigContract) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.input_prefix = processing_config.storage.input_prefix
        self.output_prefix = processing_config.storage.output_prefix
        self.embeddings_suffix = ".embedding.json"
