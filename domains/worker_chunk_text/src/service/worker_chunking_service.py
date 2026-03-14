"""Worker service that reads processed artifacts and emits chunk manifests."""

import json

from chunking.resolver import ChunkingStagesResolver
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ManifestWriter
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.helpers.run_ids import build_source_run_id
from pipeline_common.stages_contracts import FileMetadata, ProcessResult, StageArtifact
from pipeline_common.startup.contracts import WorkerService
from processor.chunk_text import ChunkTextProcessor


class WorkerChunkingService(WorkerService):
    """Poll for processed artifacts, chunk them, write manifests, and emit lineage."""

    def __init__(
        self,
        queue_gateway: QueueGateway,
        storage_gateway: ObjectStorageGateway,
        lineage_gateway: LineageRuntimeGateway,
        poll_interval_seconds: int,
        chunking_resolver: ChunkingStagesResolver,
        processor: ChunkTextProcessor,
        manifest_writer: ManifestWriter,
    ) -> None:
        """Initialize worker dependencies and queue polling configuration."""
        self._queue_gateway = queue_gateway
        self._storage_gateway = storage_gateway
        self._lineage_gateway = lineage_gateway
        self._poll_interval_seconds = poll_interval_seconds
        self._chunking_resolver = chunking_resolver
        self._processor = processor
        self._manifest_writer = manifest_writer

    def serve(self) -> None:
        """Run the worker loop until interrupted by the hosting runtime.

        Each iteration reads one queue message, loads the referenced input artifact,
        processes it into chunk artifacts, writes a manifest, and records lineage.
        """
        while True:
            message: ConsumedMessage | None = None
            lineage_started = False
            try:
                message = self._queue_gateway.wait_for_message(
                    poll_interval_seconds=self._poll_interval_seconds,
                )
                input_uri = self._input_uri_from_message(message)

                self._register_lineage_input(input_uri)
                lineage_started = True
                
                process_result: ProcessResult = self._transform_source_to_chunks(input_uri)

                self._write_manifest(process_result)
                
                self._register_manifest_output_lineage()
            except Exception as exc:
                if lineage_started:
                    self._lineage_gateway.fail_run(error_message=str(exc))
                if message is not None:
                    message.nack(requeue=False)
                continue
            message.ack()

    def _register_lineage_input(self, input_uri: str) -> None:
        """Start a lineage run and register the input artifact URI."""
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=input_uri,
            platform=DatasetPlatform.S3,
        )

    def _transform_source_to_chunks(self, input_uri: str) -> ProcessResult:
        """Load an input artifact, resolve stages, and run the chunk processor."""
        raw_payload = self._storage_gateway.read_object(uri=input_uri)
        input_artifact: StageArtifact = StageArtifact.from_dict(json.loads(raw_payload.decode("utf-8")))
        resolved_stages = self._chunking_resolver.resolve(input_artifact.root_doc_metadata.source_type)
        return self._processor.process(
            input_text=str(input_artifact.content.data),
            root_doc_metadata=input_artifact.root_doc_metadata,
            input_uri=input_uri,
            run_id=build_source_run_id(input_uri),
            stages=resolved_stages,
            stage_doc_metadata=FileMetadata.from_source_bytes(
                uri=input_uri,
                payload=raw_payload,
                default_content_type="application/json",
            ),
        )

    def _write_manifest(self, process_result: ProcessResult) -> None:
        """Write the chunk manifest for a completed processing result."""
        self._manifest_writer.write(process_result=process_result)

    def _register_manifest_output_lineage(self) -> None:
        """Register the written manifest as a lineage output."""
        manifest_uri = self._manifest_writer.manifest_uri
        self._lineage_gateway.add_output(
            name=manifest_uri,
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.complete_run()

    def _input_uri_from_message(self, message: ConsumedMessage) -> str:
        """Extract the input artifact URI from a consumed queue message."""
        envelope: Envelope = Envelope.from_dict(message.payload)
        return str(envelope.payload)
