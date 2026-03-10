from contracts.contracts import ProcessResult


class ChunkManifestFactory:
    def build(self, process_result: ProcessResult) -> dict[str, object]:
        source_metadata = process_result.source_metadata

        return {
            "schema_version": process_result.schema_version,
            "doc_id": str(source_metadata.doc_id),
            "output": {
                "status": process_result.result.status.value,
                "chunk_count_expected": process_result.result.chunk_count_expected,
                "chunk_count_written": process_result.result.chunk_count_written,
            },
            "chunks": process_result.result.chunk_entries,
        }
