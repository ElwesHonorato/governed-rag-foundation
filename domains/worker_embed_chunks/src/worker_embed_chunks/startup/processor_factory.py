"""Processor assembly for worker_embed_chunks startup."""

from __future__ import annotations

from pipeline_common.gateways.object_storage import ObjectStorageGateway
from worker_embed_chunks.services.embed_chunks_processor import EmbedChunksProcessor
from worker_embed_chunks.startup.embedding_composition import EmbeddingComposition
from worker_embed_chunks.startup.contracts import RuntimeEmbedChunksJobConfig


class EmbedChunksProcessorFactory:
    """Build the embed-chunks processor from worker runtime dependencies."""

    def build(
        self,
        *,
        embedding: EmbeddingComposition,
        object_storage: ObjectStorageGateway,
        worker_config: RuntimeEmbedChunksJobConfig,
    ) -> EmbedChunksProcessor:
        return EmbedChunksProcessor(
            embedder=embedding.embedder,
            object_storage=object_storage,
            storage_bucket=worker_config.storage.bucket,
            output_prefix=worker_config.storage.output_prefix,
        )
