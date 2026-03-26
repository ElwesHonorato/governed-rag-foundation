"""Service configuration for worker_index_elasticsearch."""

from dataclasses import dataclass

from worker_index_elasticsearch.services.indexed_chunk_document_mapper import IndexedChunkDocumentMapper


@dataclass(frozen=True)
class MapperConfig:
    index_template: IndexedChunkDocumentMapper


MAPPER = {
    "04_chunks/": MapperConfig(
        index_template=IndexedChunkDocumentMapper(),
    ),
}
