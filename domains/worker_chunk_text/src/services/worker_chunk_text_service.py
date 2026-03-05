import logging
from typing import Any

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.processing_engine import ReadGateway, WriteGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, StageQueue
from pipeline_common.helpers.contracts import utc_now_iso
from pipeline_common.startup.contracts import WorkerService
from contracts.contracts import ChunkTextProcessingConfigContract
from services.chunk_text_processor import ChunkTextProcessor

logger = logging.getLogger(__name__)


class WorkerChunkTextService(WorkerService):
    """Transform processed document payloads into chunk artifacts."""

    def __init__(
        self,
        *,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        spark_session: Any | None,
        processing_config: ChunkTextProcessingConfigContract,
    ) -> None:
        """Initialize chunking worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.spark_session = spark_session
        self.read_gateway = ReadGateway(spark_session=self.spark_session) if self.spark_session is not None else None
        self.write_gateway = WriteGateway() if self.spark_session is not None else None
        self._initialize_runtime_config(processing_config)
        self.processor = ChunkTextProcessor(
            spark_session=self.spark_session,
            object_storage=self.object_storage,
            storage_bucket=self.storage_bucket,
            output_prefix=self.output_prefix,
        )

    def serve(self) -> None:
        """Run the chunking worker loop by polling queue messages."""
        while True:
            message = self.stage_queue.pop_message()
            if message is None:
                continue
            try:
                source_key = self._source_key_from_message(message)
            except Exception:
                message.nack(requeue=True)
                logger.exception("Failed chunk invalid-message handling; requeued message")
                continue
            if source_key is None:
                continue
            try:
                self._handle_chunk_request(source_key)
            except Exception:
                if self._handle_chunk_failure(source_key):
                    message.ack()
                else:
                    message.nack(requeue=True)
                continue
            message.ack()

    def _handle_chunk_request(self, source_key: str) -> None:
        chunk_job = self._build_chunk_job(source_key)
        if chunk_job is None:
            return

        self.lineage.start_run()
        self.lineage.add_input(
            name=f"{self.storage_bucket}/{chunk_job['source_key']}",
            platform=DatasetPlatform.S3,
        )
        try:
            processed = self._read_processed_payload(chunk_job["source_key"])
            doc_id = str(processed["doc_id"])
            if self.spark_session is None:
                written, destination_keys = self.processor.write_chunk_artifacts(processed, doc_id=doc_id)
            else:
                input_record = self.processor.build_input_record(processed, doc_id=doc_id)
                input_df = self.read_gateway.from_records([input_record])
                written, destination_keys = self.processor.write_chunk_artifacts_from_dataframe(
                    input_df,
                    write_gateway=self.write_gateway,
                )
            for destination_key in destination_keys:
                self.lineage.add_output(
                    name=f"{self.storage_bucket}/{destination_key}",
                    platform=DatasetPlatform.S3,
                )

            self.lineage.complete_run()
            for destination_key in destination_keys:
                self._enqueue_chunk_object(destination_key)
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            raise

        if written is not None:
            doc_id = source_key.split("/")[-1].replace(self.processed_suffix, "")
            logger.info("Wrote %d chunk objects for doc_id '%s'", written, doc_id)

    def _send_chunk_failure(self, source_key: str) -> None:
        self.stage_queue.push_dlq(
            Envelope(
                type="chunk_text.failure",
                payload={"source_key": source_key},
            ).to_dict()
        )

    def _handle_chunk_failure(self, source_key: str) -> bool:
        """Route failed chunk request to DLQ; return True when message can be acked."""
        try:
            self._send_chunk_failure(source_key)
        except Exception:
            logger.exception(
                "Failed chunking source key '%s' and failed DLQ publish; requeueing message",
                source_key,
            )
            return False
        logger.exception("Failed chunking source key '%s'; sent to DLQ", source_key)
        return True

    def _build_chunk_job(self, source_key: str) -> dict[str, str] | None:
        if not source_key.startswith(self.input_prefix) or source_key == self.input_prefix:
            return None
        if not source_key.endswith(self.processed_suffix):
            return None
        return {"source_key": source_key}

    def _read_processed_payload(self, source_key: str) -> dict[str, Any]:
        raw_payload = self.object_storage.read_object(self.storage_bucket, source_key)
        return self.processor.read_processed_payload(raw_payload)

    def _enqueue_chunk_object(self, destination_key: str) -> None:
        self.stage_queue.push(
            Envelope(
                type="embed_chunks.request",
                payload={"storage_key": destination_key},
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
                    type="chunk_text.invalid_message",
                    payload={
                        "error": str(exc),
                        "message_payload": message.payload,
                        "failed_at": utc_now_iso(),
                    },
                ).to_dict()
            )
            message.ack()
            logger.exception("Invalid chunk queue message payload; sent to DLQ and acknowledged")
            return None

    def _initialize_runtime_config(self, processing_config: ChunkTextProcessingConfigContract) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.input_prefix = processing_config.storage.input_prefix
        self.output_prefix = processing_config.storage.output_prefix
        self.processed_suffix = ".json"
