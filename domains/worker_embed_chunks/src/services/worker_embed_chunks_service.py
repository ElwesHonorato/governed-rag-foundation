import logging
import json
from typing import Any

from contracts.contracts import EmbedChunksProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import Envelope, StageQueue
from pipeline_common.startup.contracts import WorkerService
from services.embed_chunks_processor import EmbedChunksProcessor

logger = logging.getLogger(__name__)


class WorkerEmbedChunksService(WorkerService):
    """Transform chunk artifacts into embedding payloads."""

    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        spark_session: Any | None,
        processing_config: EmbedChunksProcessingConfigContract,
        dimension: int,
    ) -> None:
        """Initialize embedding worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.spark_session = spark_session
        self._initialize_runtime_config(processing_config)
        self.dimension = dimension
        self.processor = EmbedChunksProcessor(
            dimension=self.dimension,
            spark_session=self.spark_session,
        )

    def serve(self) -> None:
        """Run the embedding worker loop by polling queue messages."""
        while True:
            source_key = self._pop_queued_source_key()
            if source_key is None:
                continue
            try:
                self._handle_embed_request(source_key)
            except Exception:
                self._send_embed_failure(source_key)
                logger.exception("Failed embedding source key '%s'; sent to DLQ", source_key)

    def _handle_embed_request(self, source_key: str) -> None:
        embed_job = self._build_embed_job(source_key)
        if embed_job is None:
            return

        self.lineage.start_run()
        self.lineage.add_input(
            name=f"{self.storage_bucket}/{embed_job['source_key']}",
            platform=DatasetPlatform.S3,
        )
        try:
            chunk_payload = self._read_chunk_payload(embed_job["source_key"])
            embedding_payload = self.processor.build_embedding_payload(chunk_payload)
            doc_id = str(embedding_payload["doc_id"])
            chunk_id = str(embedding_payload["chunk_id"])
            destination_key = self._embedding_object_key(doc_id, chunk_id)
            self.lineage.add_output(
                name=f"{self.storage_bucket}/{destination_key}",
                platform=DatasetPlatform.S3,
            )
            if self.object_storage.object_exists(self.storage_bucket, destination_key):
                self._send_embed_failure(source_key)
                self.lineage.fail_run(error_message=f"Embeddings artifact already exists: {destination_key}")
                return

            self._write_embeddings_object(destination_key, embedding_payload)
            self._enqueue_embeddings_object(destination_key, doc_id)
            self.lineage.complete_run()
            logger.info("Wrote embedding object '%s'", destination_key)
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            raise

    def _send_embed_failure(self, source_key: str) -> None:
        self.stage_queue.push_dlq(
            Envelope(
                type="embed_chunks.failure",
                payload={"source_key": source_key},
            ).to_dict()
        )

    def _build_embed_job(self, source_key: str) -> dict[str, str] | None:
        if not source_key.startswith(self.input_prefix) or source_key == self.input_prefix:
            return None
        if not source_key.endswith(self.chunks_suffix):
            return None
        return {"source_key": source_key}

    def _read_chunk_payload(self, source_key: str) -> dict[str, Any]:
        raw_payload = self.object_storage.read_object(self.storage_bucket, source_key)
        return self.processor.read_chunk_payload(raw_payload)

    def _embedding_object_key(self, doc_id: str, chunk_id: str) -> str:
        return f"{self.output_prefix}{doc_id}/{chunk_id}.embedding.json"

    def _write_embeddings_object(self, destination_key: str, payload: dict[str, Any]) -> None:
        self.object_storage.write_object(
            self.storage_bucket,
            destination_key,
            json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )

    def _enqueue_embeddings_object(self, destination_key: str, doc_id: str) -> None:
        self.stage_queue.push(
            Envelope(
                type="index_weaviate.request",
                payload={"embeddings_key": destination_key, "doc_id": doc_id},
            ).to_dict()
        )

    def _pop_queued_source_key(self) -> str | None:
        """Pop one chunks key from embedding queue when available."""
        raw = self.stage_queue.pop_message()
        if raw is None:
            return None
        envelope = Envelope.from_dict(raw)
        return str(envelope.payload["storage_key"])

    def _initialize_runtime_config(self, processing_config: EmbedChunksProcessingConfigContract) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.input_prefix = processing_config.storage.input_prefix
        self.output_prefix = processing_config.storage.output_prefix
        self.chunks_suffix = ".chunk.json"
