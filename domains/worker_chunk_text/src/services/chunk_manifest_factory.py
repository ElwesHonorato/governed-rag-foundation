from pipeline_common.provenance import sha256_hex

from contracts.chunk_manifest import (
    ChunkerConfig,
    ChunkManifest,
    ChunkManifestLineage,
    ChunkManifestOutput,
    ChunkManifestProcessing,
)
from services.chunk_text_processor import ChunkProcessResult, ChunkTextProcessor


class ChunkManifestFactory:
    def build(self, process_result: ChunkProcessResult) -> ChunkManifest:
        chunking_input_metadata = process_result.chunking_input_metadata
        source_metadata = chunking_input_metadata.source_metadata
        source_uri = chunking_input_metadata.input_dataset_urn

        lineage = ChunkManifestLineage(
            source_asset_id=source_uri,
            source_hash=sha256_hex(source_uri),
            content_type=source_metadata.content_type,
            document_hash=chunking_input_metadata.input_content_hash,
            parser_version=process_result.processor_metadata.version,
        )

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
            lineage=lineage,
            processing=processing,
            output=output,
            chunks=process_result.output.chunk_entries,
        )
