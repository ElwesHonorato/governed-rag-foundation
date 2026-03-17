"""Factory for local vector gateway construction."""

from __future__ import annotations

from pathlib import Path

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)
from agent_platform.gateways.retrieval.local_vector_search import (
    LocalVectorSearchGateway,
)


class VectorGatewayFactory:
    """Build vector gateways for local agent-platform runtime."""

    def build(
        self,
        *,
        vector_index_path: Path,
        retrieval_embedder: DeterministicHashEmbedder,
    ) -> LocalVectorSearchGateway:
        return LocalVectorSearchGateway(str(vector_index_path), retrieval_embedder)
