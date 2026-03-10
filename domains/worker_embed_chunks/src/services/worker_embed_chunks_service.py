import logging
import uuid
from typing import Any

from contracts.contracts import EmbedChunksProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.processing_engine import ReadGateway, WriteGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, StageQueue
from pipeline_common.helpers.contracts import utc_now_iso
from pipeline_common.startup.contracts import WorkerService
from services.embed_chunks_processor import ChunkArtifactPayload, EmbedChunksProcessor

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
        self.read_gateway = ReadGateway(spark_session=self.spark_session) if self.spark_session is not None else None
        self.write_gateway = WriteGateway() if self.spark_session is not None else None
        self._initialize_runtime_config(processing_config)
        self.dimension = dimension
        self.processor = EmbedChunksProcessor(
            dimension=self.dimension,
            spark_session=self.spark_session,
            object_storage=self.object_storage,
            storage_bucket=self.storage_bucket,
            output_prefix=self.output_prefix,
        )

    def serve(self) -> None:
        """Run the embedding worker loop by polling queue messages."""
        while True:
            message = self.stage_queue.pop_message()
            if message is None:
                continue
            try:
                source_key = self._source_key_from_message(message)
            except Exception:
                message.nack(requeue=True)
                logger.exception("Failed embed invalid-message handling; requeued message")
                continue
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
            embedding_run_id = uuid.uuid4().hex
            if self.spark_session is None:
                write_result = self.processor.write_embedding_artifact(
                    chunk_payload,
                    embedding_run_id=embedding_run_id,
                )
            else:
                input_record = self.processor.build_input_record(
                    chunk_payload,
                    embedding_run_id=embedding_run_id,
                )
                input_df = self.read_gateway.from_records([input_record])
                write_result = self.processor.write_embedding_artifact_from_dataframe(
                    input_df,
                    write_gateway=self.write_gateway,
                )
            doc_id = write_result.doc_id
            destination_key = write_result.destination_key
            self.lineage.add_output(
                name=f"{self.storage_bucket}/{destination_key}",
                platform=DatasetPlatform.S3,
            )
            if not write_result.wrote:
                self._send_embed_failure(source_key)
                self.lineage.fail_run(error_message=f"Embeddings artifact already exists: {destination_key}")
                return

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
        if not source_key.startswith(self.input_prefix) or source_key == self.input_prefix:
            return None
        if not source_key.endswith(self.chunks_suffix):
            return None
        return {"source_key": source_key}

    def _read_chunk_payload(self, source_key: str) -> ChunkArtifactPayload:
        raw_payload = self.object_storage.read_object(self.storage_bucket, source_key)
        return self.processor.read_chunk_payload(raw_payload, source_key=source_key)

    def _enqueue_embeddings_object(self, destination_key: str, doc_id: str) -> None:
        self.stage_queue.push(
            Envelope(
                type="index_weaviate.request",
                payload={"embeddings_key": destination_key, "doc_id": doc_id},
            ).to_dict()
        )

    def _source_key_from_message(self, message: ConsumedMessage) -> str | None:
        """Parse source key from queue payload; route invalid payloads to DLQ."""
        try:
            envelope = Envelope.from_dict(message.payload)
            return str(envelope.payload["storage_key"])
        except Exception as exc:
            self.stage_queue.push_dlq(
                Envelope(
                    type="embed_chunks.invalid_message",
                    payload={
                        "error": str(exc),
                        "message_payload": message.payload,
                        "failed_at": utc_now_iso(),
                    },
                ).to_dict()
            )
            message.ack()
            logger.exception("Invalid embed queue message payload; sent to DLQ and acknowledged")
            return None

    def _initialize_runtime_config(self, processing_config: EmbedChunksProcessingConfigContract) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.input_prefix = processing_config.storage.input_prefix
        self.output_prefix = processing_config.storage.output_prefix
        self.chunks_suffix = ".chunk.json"
