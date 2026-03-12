import logging
import uuid

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.helpers.contracts import utc_now_iso
from pipeline_common.startup.contracts import WorkerService
from services.embed_flow import EmbedWorkItem
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
        poll_interval_seconds: int,
        storage_bucket: str,
        work_item_type: type[EmbedWorkItem],
        processor: EmbedChunksProcessor,
        chunks_suffix: str = ".chunk.json",
    ) -> None:
        """Initialize embedding worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds
        self._storage_bucket = storage_bucket
        self._work_item_type = work_item_type
        self._processor = processor
        self._chunks_suffix = chunks_suffix

    def serve(self) -> None:
        """Run the embedding worker loop by polling queue messages."""
        while True:
            try:
                message = self._queue_gateway.wait_for_message(
                    poll_interval_seconds=self._poll_interval_seconds,
                )
                work_item = self._work_item_from_message(message)
                source_key = self._source_key_from_uri(work_item.uri)
                self._register_lineage_input(work_item.uri)
                chunk_payload = self._read_chunk_payload(
                    work_item.uri,
                    source_key=source_key,
                )
                output_uri = self._write_embedding_artifact(chunk_payload)
                self._enqueue_embeddings_object(uri=output_uri)
                self._register_embedding_output_lineage(uri=output_uri)
            except Exception as exc:
                self._lineage_gateway.fail_run(error_message=str(exc))
                message.nack(requeue=True)
                continue
            message.ack()

    def _register_lineage_input(self, uri: str) -> None:
        """Start a lineage run and register the source chunk artifact."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=uri,
            platform=DatasetPlatform.S3,
        )

    def _register_embedding_output_lineage(self, uri: str) -> None:
        """Register the written embedding artifact as lineage output."""
        self._lineage_gateway.add_output(
            name=uri,
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.complete_run()

    def _read_chunk_payload(self, uri: str, *, source_key: str) -> ChunkArtifactPayload:
        raw_payload = self._storage_gateway.read_object(uri=uri)
        return self._processor.read_chunk_payload(raw_payload, source_key=source_key)

    def _write_embedding_artifact(self, chunk_payload: ChunkArtifactPayload) -> str:
        """Write one embeddings artifact and return its output URI."""
        write_result = self._processor.write_embedding_artifact(
            chunk_payload,
            embedding_run_id=uuid.uuid4().hex,
        )
        logger.info("Wrote embedding object '%s'", write_result.destination_key)
        return self._processor.output_uri(write_result.destination_key)

    def _enqueue_embeddings_object(self, uri: str) -> None:
        self._queue_gateway.push(
            Envelope(
                payload=uri,
            ).to_payload
        )

    def _work_item_from_message(self, message: ConsumedMessage) -> EmbedWorkItem:
        """Parse source URI from queue payload."""
        envelope: Envelope = Envelope.from_dict(message.payload)
        return self._work_item_type(uri=str(envelope.payload))

    def _source_key_from_uri(self, uri: str) -> str:
        uri_prefix = self._storage_gateway.build_uri(self._storage_bucket, "")
        return uri.removeprefix(uri_prefix)
