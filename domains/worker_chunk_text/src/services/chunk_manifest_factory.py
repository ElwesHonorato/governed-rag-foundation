from pipeline_common.provenance import sha256_hex

from contracts.chunk_manifest import (
    ChunkerConfig,
    ChunkManifest,
    ChunkManifestLineage,
    ChunkManifestOutput,
    ChunkManifestProcessing,
)
from services.chunk_text_processor import ChunkProcessResult


class ChunkManifestFactory:
    def build(self, process_result: ChunkProcessResult) -> ChunkManifest:
        chunk_document_metadata = process_result.chunk_document_metadata
        source_uri = chunk_document_metadata.source_s3_uri

        lineage = ChunkManifestLineage(
            source_asset_id=source_uri,
            source_hash=sha256_hex(source_uri),
            content_type=process_result.content_type,
            document_hash=chunk_document_metadata.source_content_hash,
            parser_version=process_result.parser_version,
        )

        processing = ChunkManifestProcessing(
            run_id=chunk_document_metadata.chunking_run_id,
            stage=process_result.stage_name,
            timestamp=chunk_document_metadata.timestamp,
            chunker_version=process_result.chunker_version,
            run_status=(
                "complete"
                if process_result.chunk_count_written == process_result.chunk_count_expected
                else "partial"
            ),
            chunker=ChunkerConfig(
                class_name=process_result.chunker_name,
                params=dict(process_result.chunking_params),
            ),
        )

        output = ChunkManifestOutput(
            chunk_count_expected=process_result.chunk_count_expected,
            chunk_count_written=process_result.chunk_count_written,
        )

        return ChunkManifest.build(
            doc_id=chunk_document_metadata.doc_id,
            lineage=lineage,
            processing=processing,
            output=output,
            chunks=process_result.chunk_entries,
        )
