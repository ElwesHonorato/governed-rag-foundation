"""Central wrapper for text splitter configuration."""

from dataclasses import asdict
from typing import Any

from langchain_core.documents import Document
from chunking.stages import ChunkingStage


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

    def create_documents(self, **kwargs: Any) -> list[Document]:
        """Create LangChain documents from source texts."""
        return self._splitter.create_documents(**kwargs)

    def split_documents(self, **kwargs: Any) -> list[Document]:
        """Split existing LangChain documents."""
        return self._splitter.split_documents(**kwargs)
