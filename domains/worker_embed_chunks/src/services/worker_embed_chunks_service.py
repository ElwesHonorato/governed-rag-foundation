import logging
import uuid

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway, QueueMessageType
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
        poll_interval_seconds: int,
        storage_bucket: str,
        processor: EmbedChunksProcessor,
        chunks_suffix: str = ".chunk.json",
    ) -> None:
        """Initialize embedding worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds
        self._storage_bucket = storage_bucket
        self._processor = processor
        self._chunks_suffix = chunks_suffix

    def serve(self) -> None:
        """Run the embedding worker loop by polling queue messages."""
        while True:
            message = self._queue_gateway.wait_for_message(
                poll_interval_seconds=self._poll_interval_seconds,
            )
            source_uri = self._source_uri_from_message(message)
            if source_uri is None:
                continue
            try:
                self._handle_embed_request(source_uri)
            except Exception:
                if self._handle_embed_failure(source_uri):
                    message.ack()
                else:
                    message.nack(requeue=True)
                continue
            message.ack()

    def _handle_embed_request(self, source_uri: str) -> None:
        embed_job = self._build_embed_job(source_uri)
        if embed_job is None:
            return

        self._register_lineage_input(embed_job["source_uri"])
        try:
            chunk_payload = self._read_chunk_payload(
                embed_job["source_uri"],
                source_key=embed_job["source_key"],
            )
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
                self._send_embed_failure(source_uri)
                self._lineage_gateway.fail_run(error_message=f"Embeddings artifact already exists: {destination_key}")
                return

            self._enqueue_embeddings_object(destination_key, doc_id)
            self._lineage_gateway.complete_run()
            logger.info("Wrote embedding object '%s'", destination_key)
        except Exception as exc:
            self._lineage_gateway.fail_run(error_message=str(exc))
            raise

    def _register_lineage_input(self, source_uri: str) -> None:
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=source_uri,
            platform=DatasetPlatform.S3,
        )

    def _send_embed_failure(self, source_uri: str) -> None:
        self._queue_gateway.push_dlq(
            Envelope(
                type=QueueMessageType.EMBED_CHUNKS_FAILURE,
                payload={"source_uri": source_uri},
            ).to_payload
        )

    def _handle_embed_failure(self, source_uri: str) -> bool:
        """Route failed embed request to DLQ; return True when message can be acked."""
        try:
            self._send_embed_failure(source_uri)
        except Exception:
            logger.exception(
                "Failed embedding source URI '%s' and failed DLQ publish; requeueing message",
                source_uri,
            )
            return False
        logger.exception("Failed embedding source URI '%s'; sent to DLQ", source_uri)
        return True

    def _build_embed_job(self, source_uri: str) -> dict[str, str] | None:
        if not source_uri.endswith(self._chunks_suffix):
            return None
        return {
            "source_uri": source_uri,
            "source_key": self._source_key_from_uri(source_uri),
        }

    def _read_chunk_payload(self, source_uri: str, *, source_key: str) -> ChunkArtifactPayload:
        raw_payload = self._storage_gateway.read_object(uri=source_uri)
        return self._processor.read_chunk_payload(raw_payload, source_key=source_key)

    def _enqueue_embeddings_object(self, destination_key: str, doc_id: str) -> None:
        self._queue_gateway.push(
            Envelope(
                type=QueueMessageType.INDEX_WEAVIATE_REQUEST,
                payload={"embeddings_key": destination_key, "doc_id": doc_id},
            ).to_payload
        )

    def _source_uri_from_message(self, message: ConsumedMessage) -> str | None:
        """Parse source URI from queue payload; route invalid payloads to DLQ."""
        try:
            envelope: Envelope = Envelope.from_dict(message.payload)
            return str(envelope.payload["source_uri"])
        except Exception as exc:
            self._queue_gateway.push_dlq(
                Envelope(
                    type=QueueMessageType.EMBED_CHUNKS_INVALID_MESSAGE,
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

    def _source_key_from_uri(self, source_uri: str) -> str:
        uri_prefix = self._storage_gateway.build_uri(self._storage_bucket, "")
        if not source_uri.startswith(uri_prefix):
            raise ValueError(f"Chunk source URI must start with '{uri_prefix}': {source_uri}")
        return source_uri.removeprefix(uri_prefix)
