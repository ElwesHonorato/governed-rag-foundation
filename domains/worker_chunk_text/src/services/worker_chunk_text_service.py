import logging
import time
from typing import Any

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.processing_engine import ReadGateway
from pipeline_common.provenance import ProvenanceRegistryGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, StageQueue
from pipeline_common.helpers.run_ids import build_source_run_id
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
        provenance_registry: ProvenanceRegistryGateway,
        spark_session: Any | None,
        processing_config: ChunkTextProcessingConfigContract,
    ) -> None:
        """Initialize chunking worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self.provenance_registry = provenance_registry
        self.spark_session = spark_session
        self.read_gateway = ReadGateway(spark_session=self.spark_session)
        self._initialize_runtime_config(processing_config)
        self.processor = ChunkTextProcessor(
            object_storage=self.object_storage,
            provenance_registry=self.provenance_registry,
            storage_bucket=self.storage_bucket,
            output_prefix=self.output_prefix,
        )

    def serve(self) -> None:
        """Run the chunking worker loop by polling queue messages."""
        while True:
            message = self._wait_for_next_message()
            source_key = self._source_key_from_message(message)
            try:
                self._process_chunk_job(source_key)
            except Exception:
                message.nack(requeue=False)
                continue
            message.ack()

    def _wait_for_next_message(self) -> ConsumedMessage:
        """Fetch next queue message, waiting until one is available."""
        while True:
            message = self.stage_queue.pop_message()
            if message is not None:
                return message
            time.sleep(self.poll_interval_seconds)

    def _process_chunk_job(self, source_key: str) -> None:
        source_uri = f"s3a://{self.storage_bucket}/{source_key}"
        self.lineage.start_run()
        self.lineage.add_input(
            name=source_uri,
            platform=DatasetPlatform.S3,
        )
        try:
            processed_df = self.read(source_uri)
            chunking_run_id = build_source_run_id(source_uri)
            payload_df = self.processor.build_input_dataframe(processed_df)
            processed_metadata = self.processor.metadata_from_processed_dataframe(processed_df)
            written, destination_keys = self.processor.write_chunk_artifacts_from_dataframe(
                payload_df,
                doc_id=processed_metadata.doc_id,
                source_uri=source_uri,
                chunking_run_id=chunking_run_id,
            )
            registry_dataset = f"{self.storage_bucket}/07_metadata/provenance/chunking/latest/"
            self.lineage.add_output(name=registry_dataset, platform=DatasetPlatform.S3)
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

    def read(self, source_uri: str) -> Any:
        return self.read_gateway.read(path=source_uri, format_name="json")

    def _enqueue_chunk_object(self, destination_key: str) -> None:
        self.stage_queue.push(
            Envelope(
                type="embed_chunks.request",
                payload={"storage_key": destination_key},
            ).to_dict()
        )

    def _source_key_from_message(self, message: ConsumedMessage) -> str:
        """Parse source key from queue payload."""
        envelope = Envelope.from_dict(message.payload)
        return str(envelope.payload["storage_key"])

    def _initialize_runtime_config(self, processing_config: ChunkTextProcessingConfigContract) -> None:
        """Load runtime config values into worker state."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.input_prefix = processing_config.storage.input_prefix
        self.output_prefix = processing_config.storage.output_prefix
        self.processed_suffix = ".json"
