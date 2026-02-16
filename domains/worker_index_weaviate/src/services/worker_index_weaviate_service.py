
from abc import ABC, abstractmethod
import json
import logging
from typing import Any, TypedDict

from pipeline_common.lineage import LineageEmitter
from pipeline_common.queue import StageQueue
from pipeline_common.object_storage import ObjectStorageGateway
from pipeline_common.weaviate import upsert_chunk, verify_query

logger = logging.getLogger(__name__)


class WorkerService(ABC):
    """Minimal worker interface for long-running service loops."""

    @abstractmethod
    def serve(self) -> None:
        """Run the worker loop indefinitely."""


class StorageConfig(TypedDict):
    """Storage-related prefixes and bucket for indexing worker."""

    bucket: str
    embeddings_prefix: str
    indexes_prefix: str


class QueueConfig(TypedDict):
    """Queue contract and timeout settings for indexing worker."""

    stage: str
    stage_queues: dict[str, Any]
    queue_pop_timeout_seconds: int


class IndexWeaviateProcessingConfig(TypedDict):
    """Runtime config for indexing worker queues, storage, and polling."""

    poll_interval_seconds: int
    queue: QueueConfig
    storage: StorageConfig


class WorkerIndexWeaviateService(WorkerService):
    """Index embeddings artifacts into Weaviate and persist status objects."""

    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        lineage: LineageEmitter,
        processing_config: IndexWeaviateProcessingConfig,
        weaviate_url: str,
    ) -> None:
        """Initialize indexing worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.weaviate_url = weaviate_url
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        """Run the indexing worker loop by polling queue messages."""
        while True:
            request = self._pop_queued_request()
            if request is None:
                continue
            embeddings_key, doc_id = request
            try:
                self.process_embeddings_key(embeddings_key, doc_id)
            except Exception:
                self.stage_queue.push_dlq_message(embeddings_key=embeddings_key, doc_id=doc_id)
                logger.exception("Failed indexing embeddings key '%s'; sent to DLQ", embeddings_key)

    def process_embeddings_key(self, embeddings_key: str, doc_id: str) -> None:
        """Index one embedding artifact and write indexing status output."""
        if not embeddings_key.startswith(self.embeddings_prefix) or embeddings_key == self.embeddings_prefix:
            return
        if not embeddings_key.endswith(self.embeddings_suffix):
            return

        self.lineage.start_run(
            run_facets={
                "governedRag": {
                    "_producer": self.lineage.producer,
                    "_schemaURL": "https://governed-rag.dev/schemas/facets/governedRagRunFacet.json",
                    "embeddings_key": embeddings_key,
                    "doc_id": doc_id,
                }
            }
        )
        self.lineage.add_input({"name": embeddings_key})
        try:
            payload = self._read_embeddings_object(embeddings_key)
            resolved_doc_id = str(payload.get("doc_id", doc_id))
            resolved_chunk_id = str(payload.get("chunk_id", ""))
            destination_key = self._indexed_key(resolved_doc_id, resolved_chunk_id)
            self.lineage.set_run_facets(
                {
                    "governedRag": {
                        "_producer": self.lineage.producer,
                        "_schemaURL": "https://governed-rag.dev/schemas/facets/governedRagRunFacet.json",
                        "embeddings_key": embeddings_key,
                        "index_key": destination_key,
                        "doc_id": resolved_doc_id,
                        "chunk_id": resolved_chunk_id,
                    }
                }
            )
            self.lineage.add_output({"name": destination_key})
            if self._indexed_exists(destination_key):
                self.stage_queue.push_dlq_message(embeddings_key=embeddings_key, doc_id=resolved_doc_id)
                self.lineage.fail_run(error_message=f"Index status already exists: {destination_key}")
                return

            self._upsert_embeddings(payload)
            self._write_indexed_object(destination_key, resolved_doc_id, resolved_chunk_id)
            self.lineage.complete_run()
            logger.info("Wrote indexed status '%s'", destination_key)
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            raise

    def _pop_queued_request(self) -> tuple[str, str] | None:
        """Pop one indexing request from queue when available."""
        message = self.stage_queue.pop_message()
        if message is None:
            return None
        return str(message["embeddings_key"]), str(message["doc_id"])

    def _read_embeddings_object(self, source_key: str) -> dict[str, Any]:
        """Read and decode embeddings-stage payload."""
        raw_payload = self.object_storage.read_object(self.storage_bucket, source_key)
        return dict(json.loads(raw_payload.decode("utf-8", errors="ignore")))

    def _upsert_embeddings(self, payload: dict[str, Any]) -> None:
        """Upsert embedding record(s) into Weaviate."""
        if isinstance(payload.get("embeddings"), list):
            items = payload.get("embeddings", [])
        else:
            items = [payload]
        for item in items:
            metadata = dict(item.get("metadata", {}))
            chunk_id = str(item["chunk_id"])
            vector = item.get("vector", [])
            upsert_chunk(
                self.weaviate_url,
                chunk_id=chunk_id,
                vector=vector,
                properties={
                    "chunk_id": chunk_id,
                    "doc_id": metadata.get("doc_id"),
                    "chunk_text": metadata.get("chunk_text"),
                    "source_key": metadata.get("source_key"),
                    "security_clearance": metadata.get("security_clearance"),
                },
            )

    def _indexed_key(self, doc_id: str, chunk_id: str) -> str:
        """Build the indexed-stage key for one document chunk."""
        if chunk_id:
            return f"{self.indexes_prefix}{doc_id}/{chunk_id}.indexed.json"
        return f"{self.indexes_prefix}{doc_id}.indexed.json"

    def _indexed_exists(self, destination_key: str) -> bool:
        """Return whether the indexing status output already exists."""
        return self.object_storage.object_exists(self.storage_bucket, destination_key)

    def _write_indexed_object(self, destination_key: str, doc_id: str, chunk_id: str) -> None:
        """Persist indexed status payload into the indexes S3 stage."""
        status_payload: dict[str, Any] = {"doc_id": doc_id, "status": "indexed"}
        if chunk_id:
            status_payload["chunk_id"] = chunk_id
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(status_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )
        result = verify_query(self.weaviate_url, "logistics")
        logger.info("Indexed doc_id '%s' verify=%s", doc_id, bool(result))

    def _initialize_runtime_config(self, processing_config: IndexWeaviateProcessingConfig) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config["poll_interval_seconds"]
        self.storage_bucket = processing_config["storage"]["bucket"]
        self.embeddings_prefix = processing_config["storage"]["embeddings_prefix"]
        self.indexes_prefix = processing_config["storage"]["indexes_prefix"]
        self.embeddings_suffix = ".embedding.json"
