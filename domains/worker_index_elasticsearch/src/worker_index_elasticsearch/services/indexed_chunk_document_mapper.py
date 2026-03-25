"""Map chunk-stage artifacts into Elasticsearch indexed document contracts."""

from __future__ import annotations

from pipeline_common.elasticsearch import IndexedChunkDocument
from pipeline_common.stages_contracts import StageArtifact


class IndexedChunkDocumentMapper:
    """Build Elasticsearch indexed document contracts from chunk artifacts."""

    def map_document(self, *, artifact: StageArtifact, artifact_uri: str) -> IndexedChunkDocument:
        """Map one chunk artifact to the Elasticsearch document contract."""
        chunk_metadata = artifact.content_metadata
        if not isinstance(chunk_metadata, dict):
            raise ValueError("Chunk artifact metadata must be a dictionary.")
        root_metadata = artifact.root_doc_metadata
        processor_metadata = artifact.processor_metadata
        chunk_id = str(chunk_metadata["chunk_id"])
        return IndexedChunkDocument(
            document_id=chunk_id,
            chunk_id=chunk_id,
            doc_id=str(root_metadata.doc_id),
            chunk_text=str(artifact.content.data),
            source_uri=str(root_metadata.uri),
            artifact_uri=artifact_uri,
            content_type=str(root_metadata.content_type),
            created_at=str(root_metadata.timestamp),
            security_clearance=str(root_metadata.security_clearance),
            source_type=str(root_metadata.source_type),
            chunk_text_hash=str(chunk_metadata.get("chunk_text_hash", "")),
            offsets_start=int(chunk_metadata.get("offsets_start", 0)),
            offsets_end=int(chunk_metadata.get("offsets_end", 0)),
            processor_name=str(processor_metadata.name),
            processor_version=str(processor_metadata.version),
            metadata={
                "chunk_index": int(chunk_metadata.get("index", 0)),
                "params": artifact.params,
                "stage_doc_uri": str(artifact.stage_doc_metadata.uri),
            },
        )
