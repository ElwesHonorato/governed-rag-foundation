import json

from configs.chunking_scaffold import ChunkingStagesResolver
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.gateways.queue import ConsumedMessage, Envelope, QueueGateway
from pipeline_common.helpers.run_ids import build_source_run_id
from pipeline_common.stages_contracts import StageArtifact
from pipeline_common.startup.contracts import WorkerService
from contracts.contracts import ProcessResult
from services.chunk_manifest_writer import ChunkManifestWriter
from services.chunk_text_processor import ChunkTextProcessor


class WorkerChunkingService(WorkerService):
    """Transform processed document payloads into chunk artifacts."""

    def __init__(
        self,
        queue_gateway: QueueGateway,
        storage_gateway: ObjectStorageGateway,
        lineage_gateway: LineageRuntimeGateway,
        poll_interval_seconds: int,
        chunking_resolver: ChunkingStagesResolver,
        processor: ChunkTextProcessor,
        manifest_writer: ChunkManifestWriter,
    ) -> None:
        """Initialize chunking worker dependencies and runtime settings."""
        self._queue_gateway = queue_gateway
        self._storage_gateway = storage_gateway
        self._lineage_gateway = lineage_gateway
        self._poll_interval_seconds = poll_interval_seconds
        self._chunking_resolver = chunking_resolver
        self._processor = processor
        self._manifest_writer = manifest_writer

    def serve(self) -> None:
        """Run the chunking worker loop by polling queue messages."""
        while True:
            try:
                message = self._queue_gateway.wait_for_message(
                    poll_interval_seconds=self._poll_interval_seconds,
                )
                source_uri = self._source_uri_from_message(message)

                self._register_lineage_input(source_uri)
                
                process_result: ProcessResult = self._transform_source_to_chunks(source_uri)

                self._write_manifest(process_result)
                
                self._register_manifest_output_lineage()
            except Exception as exc:
                self._lineage_gateway.fail_run(error_message=str(exc))
                message.nack(requeue=False)
                continue
            message.ack()

    def _register_lineage_input(self, source_uri: str) -> None:
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=source_uri,
            platform=DatasetPlatform.S3,
        )

    def _transform_source_to_chunks(self, source_uri: str) -> ProcessResult:
        raw_payload = self._storage_gateway.read_object(source_uri)
        input_artifact: StageArtifact = StageArtifact.from_dict(json.loads(raw_payload.decode("utf-8")))
        resolved_stages = self._chunking_resolver.resolve(input_artifact.source_metadata.source_type)
        return self._processor.process(
            input_artifact=input_artifact,
            source_uri=source_uri,
            run_id=build_source_run_id(source_uri),
            stages=resolved_stages,
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

    def _source_uri_from_message(self, message: ConsumedMessage) -> str:
        """Parse source URI from queue payload."""
        envelope: Envelope = Envelope.from_dict(message.payload)
        return str(envelope.payload["source_uri"])
