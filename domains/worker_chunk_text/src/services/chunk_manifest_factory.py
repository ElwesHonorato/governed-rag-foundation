from contracts.contracts import (
    CHUNK_MANIFEST_SCHEMA_VERSION,
    ChunkProcessResult,
)


class ChunkManifestFactory:
    def build(self, process_result: ChunkProcessResult) -> dict[str, object]:
        source_metadata = process_result.source_metadata

        return {
            "schema_version": CHUNK_MANIFEST_SCHEMA_VERSION,
            "doc_id": str(source_metadata.doc_id),
            "output": {
                "chunk_count_expected": process_result.output.chunk_count_expected,
                "chunk_count_written": process_result.output.chunk_count_written,
            },
            "chunks": list(process_result.output.chunk_entries),
        }
