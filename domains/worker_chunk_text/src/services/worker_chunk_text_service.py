import logging
import json
import time

from configs.chunking_scaffold import ChunkingStagesResolver
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.helpers.run_ids import build_source_run_id
from pipeline_common.stages_contracts import Content, StageArtifact
from pipeline_common.startup.contracts import WorkerService
from contracts.contracts import ChunkTextStorageConfigContract
from services.chunk_manifest_writer import ChunkManifestWriter
from services.chunk_text_processor import ChunkTextProcessor

logger = logging.getLogger(__name__)


class WorkerChunkTextService(WorkerService):
    """Transform processed document payloads into chunk artifacts."""

    def __init__(
        self,
        queue_gateway: QueueGateway,
        storage_gateway: ObjectStorageGateway,
        lineage_gateway: LineageRuntimeGateway,
        env: str | None,
        poll_interval_seconds: int,
        storage_config: ChunkTextStorageConfigContract,
    ) -> None:
        """Initialize chunking worker dependencies and runtime settings."""
        self._queue_gateway = queue_gateway
        self._storage_gateway = storage_gateway
        self._lineage_gateway = lineage_gateway
        self._env = env
        self._poll_interval_seconds = poll_interval_seconds
        self._storage_config = storage_config

    def _init_runtime_components(self) -> None:
        self._chunking_resolver = ChunkingStagesResolver()
        self.processor = ChunkTextProcessor(
            object_storage=self._storage_gateway,
            storage_bucket=self._storage_config.bucket,
            output_prefix=self._storage_config.output_prefix,
        )
        self.manifest_writer = ChunkManifestWriter(
            object_storage=self._storage_gateway,
            storage_bucket=self._storage_config.bucket,
            manifest_prefix=self._storage_config.manifest_prefix,
        )

    def serve(self) -> None:
        """Run the chunking worker loop by polling queue messages."""
        self._init_runtime_components()
        while True:
            message = self._wait_for_next_message()
            source_uri = self._source_uri_from_message(message)
            try:
                self._process_chunk_job(source_uri)
            except Exception:
                message.nack(requeue=False)
                continue
            message.ack()

    def _wait_for_next_message(self) -> ConsumedMessage:
        """Fetch next queue message, waiting until one is available."""
        while True:
            message = self._queue_gateway.pop_message()
            if message is not None:
                return message
            time.sleep(self._poll_interval_seconds)

    def _process_chunk_job(self, source_uri: str) -> None:
        source_key = self._source_key_from_uri(source_uri)
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=source_uri,
            platform=DatasetPlatform.S3,
        )
        try:
            raw_payload = self._storage_gateway.read_object(self._storage_config.bucket, source_key)
            input_artifact = StageArtifact.from_dict(
                json.loads(raw_payload.decode("utf-8")),
                content_type=Content,
            )
            resolved_stages = self._chunking_resolver.resolve(input_artifact.source_metadata.source_type)
            process_result = self.processor.process(
                input_artifact=input_artifact,
                source_uri=source_uri,
                run_id=build_source_run_id(source_uri),
                stages=resolved_stages,
            )
            self.manifest_writer.write(process_result=process_result)
            self._lineage_gateway.complete_run()
        except Exception as exc:
            self._lineage_gateway.fail_run(error_message=str(exc))
            raise

    def _send_chunk_failure(self, source_key: str) -> None:
        self._queue_gateway.push_dlq(
            Envelope(
                type="chunk_text.failure",
                payload={"source_key": source_key},
            ).to_payload
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

    def _source_uri_from_message(self, message: ConsumedMessage) -> str:
        """Parse source URI from queue payload."""
        envelope = Envelope.from_dict(message.payload)
        return str(envelope.payload["source_uri"])

    def _source_key_from_uri(self, source_uri: str) -> str:
        bucket_prefix = "s3a://{bucket}/".format(bucket=self._storage_config.bucket)
        if not source_uri.startswith(bucket_prefix):
            raise ValueError("source_uri must start with the configured storage bucket prefix.")
        return source_uri.removeprefix(bucket_prefix)
