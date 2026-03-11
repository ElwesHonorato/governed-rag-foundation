import logging
import uuid
import time

from contracts.contracts import EmbedChunksProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.helpers.contracts import utc_now_iso
from pipeline_common.startup.contracts import WorkerService
from services.embed_chunks_processor import ChunkArtifactPayload, EmbedChunksProcessor

logger = logging.getLogger(__name__)


class WorkerEmbedChunksService(WorkerService):
    """Transform chunk artifacts into embedding payloads."""

    def __init__(
        self,
        *,
        stage_queue: QueueGateway,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        processing_config: EmbedChunksProcessingConfigContract,
        dimension: int,
    ) -> None:
        """Initialize embedding worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._initialize_runtime_config(processing_config)
        self._dimension = dimension

    def _init_runtime_components(self) -> None:
        self._processor = EmbedChunksProcessor(
            dimension=self._dimension,
            object_storage=self._storage_gateway,
            storage_bucket=self._storage_bucket,
            output_prefix=self._output_prefix,
        )

    def serve(self) -> None:
        """Run the embedding worker loop by polling queue messages."""
        self._init_runtime_components()
        while True:
            message = self._wait_for_next_message()
            source_key = self._source_key_from_message(message)
            if source_key is None:
                continue
            try:
                self._handle_embed_request(source_key)
            except Exception:
                if self._handle_embed_failure(source_key):
                    message.ack()
                else:
                    message.nack(requeue=True)
                continue
            message.ack()

    def _wait_for_next_message(self) -> ConsumedMessage:
        """Fetch next queue message, waiting until one is available."""
        while True:
            message = self._queue_gateway.pop_message()
            if message is not None:
                return message
            time.sleep(self._poll_interval_seconds)

    def _handle_embed_request(self, source_key: str) -> None:
        embed_job = self._build_embed_job(source_key)
        if embed_job is None:
            return

        self._register_lineage_input(embed_job["source_key"])
        try:
            chunk_payload = self._read_chunk_payload(embed_job["source_key"])
            embedding_run_id = uuid.uuid4().hex
            write_result = self._processor.write_embedding_artifact(
                chunk_payload,
                embedding_run_id=embedding_run_id,
            )
            doc_id = write_result.doc_id
            destination_key = write_result.destination_key
            self._lineage_gateway.add_output(
                name=f"{self._storage_bucket}/{destination_key}",
                platform=DatasetPlatform.S3,
            )
            if not write_result.wrote:
                self._send_embed_failure(source_key)
                self._lineage_gateway.fail_run(error_message=f"Embeddings artifact already exists: {destination_key}")
                return

            self._enqueue_embeddings_object(destination_key, doc_id)
            self._lineage_gateway.complete_run()
            logger.info("Wrote embedding object '%s'", destination_key)
        except Exception as exc:
            self._lineage_gateway.fail_run(error_message=str(exc))
            raise

    def _register_lineage_input(self, source_key: str) -> None:
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=f"{self._storage_bucket}/{source_key}",
            platform=DatasetPlatform.S3,
        )

    def _send_embed_failure(self, source_key: str) -> None:
        self._queue_gateway.push_dlq(
            Envelope(
                type="embed_chunks.failure",
                payload={"source_key": source_key},
            ).to_payload
        )

    def _handle_embed_failure(self, source_key: str) -> bool:
        """Route failed embed request to DLQ; return True when message can be acked."""
        try:
            self._send_embed_failure(source_key)
        except Exception:
            logger.exception(
                "Failed embedding source key '%s' and failed DLQ publish; requeueing message",
                source_key,
            )
            return False
        logger.exception("Failed embedding source key '%s'; sent to DLQ", source_key)
        return True

    def _build_embed_job(self, source_key: str) -> dict[str, str] | None:
        if not source_key.endswith(self._chunks_suffix):
            return None
        return {"source_key": source_key}

    def _read_chunk_payload(self, source_key: str) -> ChunkArtifactPayload:
        source_uri = "s3a://{bucket}/{source_key}".format(
            bucket=self._storage_bucket,
            source_key=source_key,
        )
        raw_payload = self._storage_gateway.read_object(source_uri)
        return self._processor.read_chunk_payload(raw_payload, source_key=source_key)

    def _enqueue_embeddings_object(self, destination_key: str, doc_id: str) -> None:
        self._queue_gateway.push(
            Envelope(
                type="index_weaviate.request",
                payload={"embeddings_key": destination_key, "doc_id": doc_id},
            ).to_payload
        )

    def _source_key_from_message(self, message: ConsumedMessage) -> str | None:
        """Parse source key from queue payload; route invalid payloads to DLQ."""
        try:
            envelope = Envelope.from_dict(message.payload)
            return str(envelope.payload["storage_key"])
        except Exception as exc:
            self._queue_gateway.push_dlq(
                Envelope(
                    type="embed_chunks.invalid_message",
                    payload={
                        "error": str(exc),
                        "message_payload": message.payload,
                        "failed_at": utc_now_iso(),
                    },
                ).to_payload
            )
            message.ack()
            logger.exception("Invalid embed queue message payload; sent to DLQ and acknowledged")
            return None

    def _initialize_runtime_config(self, processing_config: EmbedChunksProcessingConfigContract) -> None:
        """Load runtime config values into worker state."""
        self._poll_interval_seconds = processing_config.poll_interval_seconds
        self._storage_bucket = processing_config.storage.bucket
        self._output_prefix = processing_config.storage.output_prefix
        self._chunks_suffix = ".chunk.json"
