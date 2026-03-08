"""Central wrapper for text splitter configuration."""

from dataclasses import asdict
from typing import Any

from configs.chunking_scaffold import ChunkingStage


class CentralTextSplitter:
    """Single entrypoint for chunk splitter creation and usage."""

    def __init__(self, *, stage: ChunkingStage) -> None:
        self._splitter = self._build_splitter(
            chunker=stage.processor.value,
            params=asdict(stage.params),
        )

    def _build_splitter(
        self,
        *,
        chunker: type[Any],
        params: dict[str, Any],
    ) -> Any:
        return chunker(**params)

    def create_documents(self, **kwargs: Any) -> list[Any]:
        """Create LangChain documents from source texts."""
        return self._splitter.create_documents(**kwargs)

    def split_documents(self, **kwargs: Any) -> list[Any]:
        """Split existing LangChain documents."""
        return self._splitter.split_documents(**kwargs)
