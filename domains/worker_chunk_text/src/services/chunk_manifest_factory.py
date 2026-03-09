from contracts.contracts import (
    ChunkerConfig,
    ChunkManifest,
    ChunkManifestOutput,
    ChunkManifestProcessing,
    ChunkProcessResult,
)
from services.chunk_text_processor import ChunkTextProcessor


class ChunkManifestFactory:
    def build(self, process_result: ChunkProcessResult) -> ChunkManifest:
        source_metadata = process_result.source_metadata

        processing = ChunkManifestProcessing(
            run_id=process_result.run_id,
            stage=process_result.processor_metadata.stage_name,
            timestamp=source_metadata.timestamp,
            chunker_version=ChunkTextProcessor.VERSION,
            run_status=(
                "complete"
                if process_result.output.chunk_count_written == process_result.output.chunk_count_expected
                else "partial"
            ),
            chunker=ChunkerConfig(
                class_name=str(process_result.output.chunking_params["stages"][-1]["processor"]),
                params=dict(process_result.output.chunking_params),
            ),
        )

        output = ChunkManifestOutput(
            chunk_count_expected=process_result.output.chunk_count_expected,
            chunk_count_written=process_result.output.chunk_count_written,
        )

        return ChunkManifest.build(
            doc_id=source_metadata.doc_id,
            processing=processing,
            output=output,
            chunks=process_result.output.chunk_entries,
        )
