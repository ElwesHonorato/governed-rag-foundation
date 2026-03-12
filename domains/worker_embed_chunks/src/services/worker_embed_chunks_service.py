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
            message = self._queue_gateway.wait_for_message(
                poll_interval_seconds=self._poll_interval_seconds,
            )
            work_item = self._work_item_from_message(message)
            if work_item is None:
                continue
            try:
                self._handle_embed_request(work_item)
            except Exception:
                if self._handle_embed_failure(work_item):
                    message.ack()
                else:
                    message.nack(requeue=True)
                continue
            message.ack()

    def _handle_embed_request(self, work_item: EmbedWorkItem) -> None:
        if not work_item.uri.endswith(self._chunks_suffix):
            return

        source_key = self._source_key_from_uri(work_item.uri)
        self._register_lineage_input(work_item.uri)
        try:
            chunk_payload = self._read_chunk_payload(
                work_item.uri,
                source_key=source_key,
            )
            embedding_run_id = uuid.uuid4().hex
            write_result = self._processor.write_embedding_artifact(
                chunk_payload,
                embedding_run_id=embedding_run_id,
            )
            destination_key = write_result.destination_key
            self._lineage_gateway.add_output(
                name=self._processor.destination_name(destination_key),
                platform=DatasetPlatform.S3,
            )
            if not write_result.wrote:
                self._send_embed_failure(work_item)
                self._lineage_gateway.fail_run(error_message=f"Embeddings artifact already exists: {destination_key}")
                return

            self._enqueue_embeddings_object(destination_key)
            self._lineage_gateway.complete_run()
            logger.info("Wrote embedding object '%s'", destination_key)
        except Exception as exc:
            self._lineage_gateway.fail_run(error_message=str(exc))
            raise

    def _register_lineage_input(self, uri: str) -> None:
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=uri,
            platform=DatasetPlatform.S3,
        )

    def _send_embed_failure(self, work_item: EmbedWorkItem) -> None:
        self._queue_gateway.push_dlq(
            Envelope(
                payload={"uri": work_item.uri},
            ).to_payload
        )

    def _handle_embed_failure(self, work_item: EmbedWorkItem) -> bool:
        """Route failed embed request to DLQ; return True when message can be acked."""
        try:
            self._send_embed_failure(work_item)
        except Exception:
            logger.exception(
                "Failed embedding source URI '%s' and failed DLQ publish; requeueing message",
                work_item.uri,
            )
            return False
        logger.exception("Failed embedding source URI '%s'; sent to DLQ", work_item.uri)
        return True

    def _read_chunk_payload(self, uri: str, *, source_key: str) -> ChunkArtifactPayload:
        raw_payload = self._storage_gateway.read_object(uri=uri)
        return self._processor.read_chunk_payload(raw_payload, source_key=source_key)

    def _enqueue_embeddings_object(self, destination_key: str) -> None:
        destination_uri = self._processor.destination_uri(destination_key)
        self._queue_gateway.push(
            Envelope(
                payload=destination_uri,
            ).to_payload
        )

    def _work_item_from_message(self, message: ConsumedMessage) -> EmbedWorkItem | None:
        """Parse source URI from queue payload; route invalid payloads to DLQ."""
        try:
            envelope: Envelope = Envelope.from_dict(message.payload)
            return self._work_item_type(uri=str(envelope.payload))
        except Exception as exc:
            self._queue_gateway.push_dlq(
                Envelope(
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

    def _source_key_from_uri(self, uri: str) -> str:
        uri_prefix = self._storage_gateway.build_uri(self._storage_bucket, "")
        if not uri.startswith(uri_prefix):
            raise ValueError(f"Chunk source URI must start with '{uri_prefix}': {uri}")
        return uri.removeprefix(uri_prefix)
