import logging
from pathlib import Path
from typing import Any

from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.stages_contracts import ProcessResult, ProcessorContext, RootDocumentMetadata
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata
from services.index_flow import IndexStatusWriter, IndexWorkItem
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
        processor: IndexWeaviateProcessor,
        status_writer: IndexStatusWriter,
        weaviate_url: str,
        embeddings_suffix: str = ".embedding.json",
    ) -> None:
        """Initialize indexing worker dependencies and runtime settings."""
        self._queue_gateway = stage_queue
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._weaviate_url = weaviate_url
        self._poll_interval_seconds = poll_interval_seconds
        self._processor = processor
        self._status_writer = status_writer
        self._embeddings_suffix = embeddings_suffix

    def serve(self) -> None:
        """Run the indexing worker loop by polling queue messages."""
        while True:
            try:
                message = self._queue_gateway.wait_for_message(
                    poll_interval_seconds=self._poll_interval_seconds,
                )
                work_item = self._work_item_from_message(message)
                self._register_lineage_input(work_item.uri)
                payload = self._read_embeddings_payload(work_item.uri)
                process_result: ProcessResult = self._index_embeddings_payload(
                    payload=payload,
                    input_uri=work_item.uri,
                )
                self._register_index_output_lineage(self._output_uri_from_process_result(process_result))
            except Exception as exc:
                self._lineage_gateway.fail_run(error_message=str(exc))
                message.nack(requeue=True)
                continue
            message.ack()

    def _register_lineage_input(self, uri: str) -> None:
        """Start a lineage run and register the source embeddings artifact."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=uri,
            platform=DatasetPlatform.S3,
        )

    def _register_index_output_lineage(self, uri: str) -> None:
        """Register the written index status artifact as lineage output."""
        self._lineage_gateway.add_output(
            name=uri,
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.complete_run()

    def _read_embeddings_payload(self, uri: str) -> dict[str, Any]:
        raw_payload = self._storage_gateway.read_object(uri=uri)
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
        self._status_writer.write(
            destination_key=destination_key,
            payload=status_payload,
        )
        result = verify_query(self._weaviate_url, "logistics")
        logger.info("Indexed doc_id '%s' verify=%s", doc_id, bool(result))

    def _index_embeddings_payload(
        self,
        *,
        payload: dict[str, Any],
        input_uri: str,
    ) -> ProcessResult:
        """Index one embeddings payload and return the process result."""
        resolved_doc_id = str(payload.get("doc_id", ""))
        resolved_chunk_id = str(payload.get("chunk_id", ""))
        destination_key = self._processor.build_indexed_key(resolved_doc_id, resolved_chunk_id)
        self._upsert_embeddings(payload)
        self._write_indexed_object(destination_key, resolved_doc_id, resolved_chunk_id)
        metadata = dict(payload.get("metadata", {}))
        source_key = str(metadata.get("source_key") or "")
        return ProcessResult(
            run_id=resolved_chunk_id or resolved_doc_id,
            root_metadata=RootDocumentMetadata.build(
                doc_id=resolved_doc_id,
                source_key=source_key,
                timestamp=str(metadata.get("timestamp") or ""),
                security_clearance=str(metadata.get("security_clearance") or ""),
                source_type=Path(source_key).suffix.lower().lstrip("."),
                content_type="application/json",
                source_content_hash="",
            ),
            input_uri=input_uri,
            processor_context=ProcessorContext(params_hash="", params=[]),
            processor=ProcessorMetadata(name="IndexWeaviateProcessor", version="1.0.0"),
            result={
                "destination_key": destination_key,
                "output_uri": self._processor.output_uri(destination_key),
            },
        )

    def _output_uri_from_process_result(self, process_result: ProcessResult) -> str:
        """Extract the written output URI from the process result."""
        return str(process_result.result["output_uri"])

    def _work_item_from_message(self, message: ConsumedMessage) -> IndexWorkItem:
        """Parse index request from queue payload."""
        envelope: Envelope = Envelope.from_dict(message.payload)
        return IndexWorkItem(uri=str(envelope.payload))
