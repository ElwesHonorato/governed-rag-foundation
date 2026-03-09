import logging
import json
import time

from configs.chunking_scaffold import ChunkingScaffoldResolver
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, StageQueue
from pipeline_common.helpers.run_ids import build_source_run_id
from pipeline_common.stages_contracts import ArtifactPayload, ParsedTextPayload
from pipeline_common.startup.contracts import WorkerService
from contracts.contracts import ChunkTextProcessingConfigContract
from services.chunk_manifest_factory import ChunkManifestFactory
from services.chunk_manifest_writer import ChunkManifestWriter
from services.chunk_text_processor import ChunkTextProcessor

logger = logging.getLogger(__name__)


class WorkerChunkTextService(WorkerService):
    """Transform processed document payloads into chunk artifacts."""

    def __init__(
        self,
        stage_queue: StageQueue,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        processing_config: ChunkTextProcessingConfigContract,
    ) -> None:
        """Initialize chunking worker dependencies and runtime settings."""
        self.stage_queue = stage_queue
        self.object_storage = object_storage
        self.lineage = lineage
        self._chunking_resolver = ChunkingScaffoldResolver()
        self._initialize_runtime_config(processing_config)
        self.processor = ChunkTextProcessor(
            object_storage=self.object_storage,
            storage_bucket=self.storage_bucket,
            output_prefix=self.output_prefix,
        )
        self.manifest_factory = ChunkManifestFactory()
        self.manifest_writer = ChunkManifestWriter(
            object_storage=self.object_storage,
            storage_bucket=self.storage_bucket,
            manifest_prefix=self.output_prefix,
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
            raw_payload = self.object_storage.read_object(self.storage_bucket, source_key)
            payload = json.loads(raw_payload.decode("utf-8"))
            processed_payload = ArtifactPayload.from_dict(payload, content_type=ParsedTextPayload)
            resolved_stages = self._chunking_resolver.resolve(processed_payload.source_metadata.source_type)
            process_result = self.processor.process(
                processed_payload,
                source_uri=source_uri,
                run_id=build_source_run_id(source_uri),
                stages=resolved_stages,
            )
            manifest = self.manifest_factory.build(process_result)
            self.manifest_writer.write(
                manifest=manifest,
                doc_id=process_result.source_metadata.doc_id,
                run_id=process_result.run_id,
            )
            self.lineage.complete_run()
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            raise

        if process_result.result.chunk_count_written is not None:
            doc_id = source_key.split("/")[-1].replace(self.processed_suffix, "")
            logger.info(
                "Wrote %d chunk objects for doc_id '%s'",
                process_result.result.chunk_count_written,
                doc_id,
            )

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
