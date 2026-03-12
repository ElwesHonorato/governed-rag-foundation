import logging
import json
from typing import Any

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway, QueueMessageType
from pipeline_common.helpers.contracts import utc_now_iso
from services.weaviate_gateway import upsert_chunk, verify_query
from pipeline_common.startup.contracts import WorkerService
from services.index_weaviate_processor import IndexWeaviateProcessor

logger = logging.getLogger(__name__)


class WorkerIndexWeaviateService(WorkerService):
    """Index embeddings artifacts into Weaviate and persist status objects."""

    def __init__(
        self,
        *,
        stage_queue: QueueGateway,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        poll_interval_seconds: int,
        storage_bucket: str,
        processor: IndexWeaviateProcessor,
        weaviate_url: str,
        embeddings_suffix: str = ".embedding.json",
    ) -> None:
        """Initialize indexing worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._weaviate_url = weaviate_url
        self._poll_interval_seconds = poll_interval_seconds
        self._storage_bucket = storage_bucket
        self._processor = processor
        self._embeddings_suffix = embeddings_suffix

    def serve(self) -> None:
        """Run the indexing worker loop by polling queue messages."""
        while True:
            message = self._queue_gateway.wait_for_message(
                poll_interval_seconds=self._poll_interval_seconds,
            )
            request = self._request_from_message(message)
            if request is None:
                continue
            embeddings_key, doc_id = request
            try:
                self._handle_index_request(embeddings_key, doc_id)
            except Exception:
                if self._handle_index_failure(embeddings_key, doc_id):
                    message.ack()
                else:
                    message.nack(requeue=True)
                continue
            message.ack()

    def _handle_index_request(self, embeddings_key: str, doc_id: str) -> None:
        index_job = self._build_index_job(embeddings_key, doc_id)
        if index_job is None:
            return

        self._register_lineage_input(index_job["embeddings_key"])
        try:
            payload = self._read_embeddings_payload(index_job["embeddings_key"])
            resolved_doc_id = str(payload.get("doc_id", index_job["doc_id"]))
            resolved_chunk_id = str(payload.get("chunk_id", ""))
            destination_key = self._processor.build_indexed_key(resolved_doc_id, resolved_chunk_id)
            self._lineage_gateway.add_output(
                name=f"{self._storage_bucket}/{destination_key}",
                platform=DatasetPlatform.S3,
            )
            if self._storage_gateway.object_exists(self._storage_bucket, destination_key):
                self._send_index_failure(index_job["embeddings_key"], resolved_doc_id)
                self._lineage_gateway.fail_run(error_message=f"Index status already exists: {destination_key}")
                return

            self._upsert_embeddings(payload)
            self._write_indexed_object(destination_key, resolved_doc_id, resolved_chunk_id)
            self._lineage_gateway.complete_run()
            logger.info("Wrote indexed status '%s'", destination_key)
        except Exception as exc:
            self._lineage_gateway.fail_run(error_message=str(exc))
            raise

    def _register_lineage_input(self, embeddings_key: str) -> None:
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=f"{self._storage_bucket}/{embeddings_key}",
            platform=DatasetPlatform.S3,
        )

    def _send_index_failure(self, embeddings_key: str, doc_id: str) -> None:
        self._queue_gateway.push_dlq(
            Envelope(
                type=QueueMessageType.INDEX_WEAVIATE_FAILURE,
                payload={"embeddings_key": embeddings_key, "doc_id": doc_id},
            ).to_payload
        )

    def _handle_index_failure(self, embeddings_key: str, doc_id: str) -> bool:
        """Route failed index request to DLQ; return True when message can be acked."""
        try:
            self._send_index_failure(embeddings_key, doc_id)
        except Exception:
            logger.exception(
                "Failed indexing embeddings key '%s' and failed DLQ publish; requeueing message",
                embeddings_key,
            )
            return False
        logger.exception("Failed indexing embeddings key '%s'; sent to DLQ", embeddings_key)
        return True

    def _build_index_job(self, embeddings_key: str, doc_id: str) -> dict[str, str] | None:
        if not embeddings_key.endswith(self._embeddings_suffix):
            return None
        return {"embeddings_key": embeddings_key, "doc_id": doc_id}

    def _read_embeddings_payload(self, embeddings_key: str) -> dict[str, Any]:
        source_uri = "s3a://{bucket}/{source_key}".format(
            bucket=self._storage_bucket,
            source_key=embeddings_key,
        )
        raw_payload = self._storage_gateway.read_object(source_uri)
        return self._processor.read_embeddings_payload(raw_payload)

    def _upsert_embeddings(self, payload: dict[str, Any]) -> None:
        items = self._processor.build_upsert_items(payload)
        for item in items:
            properties = dict(item.get("properties", {}))
            vector = list(item.get("vector", []))
            chunk_id = str(item["chunk_id"])
            upsert_chunk(
                self._weaviate_url,
                chunk_id=chunk_id,
                vector=vector,
                properties=properties,
            )

    def _write_indexed_object(self, destination_key: str, doc_id: str, chunk_id: str) -> None:
        status_payload = self._processor.build_index_status_payload(doc_id, chunk_id)
        self._storage_gateway.write_object(
            self._storage_bucket,
            destination_key,
            json.dumps(status_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
            content_type="application/json",
        )
        result = verify_query(self._weaviate_url, "logistics")
        logger.info("Indexed doc_id '%s' verify=%s", doc_id, bool(result))

    def _request_from_message(self, message: ConsumedMessage) -> tuple[str, str] | None:
        """Parse index request from queue payload; route invalid payloads to DLQ."""
        try:
            envelope: Envelope = Envelope.from_dict(message.payload)
            return str(envelope.payload["embeddings_key"]), str(envelope.payload["doc_id"])
        except Exception as exc:
            self._queue_gateway.push_dlq(
                Envelope(
                    type=QueueMessageType.INDEX_WEAVIATE_INVALID_MESSAGE,
                    payload={
                        "error": str(exc),
                        "message_payload": message.payload,
                        "failed_at": utc_now_iso(),
                    },
                ).to_payload
            )
            message.ack()
            logger.exception("Invalid index queue message payload; sent to DLQ and acknowledged")
            return None
