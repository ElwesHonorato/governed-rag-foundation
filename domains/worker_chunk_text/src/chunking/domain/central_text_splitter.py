"""Central wrapper for recursive text splitting configuration."""

from typing import Any

from contracts.chunking_strategy import ChunkingStrategy
from langchain_text_splitters import RecursiveCharacterTextSplitter


class CentralTextSplitter:
    """Single entrypoint for recursive chunk splitter creation and usage."""

    def __init__(
        self,
        *,
        strategy: ChunkingStrategy,
        chunk_size: int,
        chunk_overlap: int,
        add_start_index: bool = False,
    ) -> None:
        self._splitter = self._build_splitter(
            strategy=strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=add_start_index,
        )

    def _build_splitter(
        self,
        *,
        strategy: ChunkingStrategy,
        chunk_size: int,
        chunk_overlap: int,
        add_start_index: bool,
    ) -> RecursiveCharacterTextSplitter:
        splitter_cls = self._splitter_registry().get(strategy)
        return splitter_cls(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=add_start_index,
        )

    def _splitter_registry(self) -> dict[ChunkingStrategy, type[RecursiveCharacterTextSplitter]]:
        return {
            ChunkingStrategy.RECURSIVE_CHARACTER: RecursiveCharacterTextSplitter,
        }

    def split_text(self, text: str) -> list[str]:
        """Split plain text into non-empty chunks."""
        return [chunk for chunk in self._splitter.split_text(text) if chunk.strip()]

    def create_documents(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> list[Any]:
        """Create LangChain documents from source texts."""
        return self._splitter.create_documents(texts, metadatas=metadatas)
