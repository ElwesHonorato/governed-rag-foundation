"""Central wrapper for recursive text splitting configuration."""

from typing import Any

from contracts.contracts import ChunkingParamsContract
from contracts.chunking_strategy import ChunkingStrategy
from langchain_text_splitters import RecursiveCharacterTextSplitter


class CentralTextSplitter:
    """Single entrypoint for recursive chunk splitter creation and usage."""

    def __init__(
        self,
        *,
        chunking_params: ChunkingParamsContract,
    ) -> None:
        self._splitter = self._build_splitter(
            chunking_params=chunking_params,
        )

    def _build_splitter(
        self,
        *,
        chunking_params: ChunkingParamsContract,
    ) -> RecursiveCharacterTextSplitter:
        splitter_cls = self._splitter_registry().get(
            chunking_params.chunk_method
        )
        splitter_kwargs = chunking_params.splitter_kwargs
        return splitter_cls(**splitter_kwargs)

    def _splitter_registry(self) -> dict[ChunkingStrategy, type[RecursiveCharacterTextSplitter]]:
        return {
            ChunkingStrategy.RECURSIVE_CHARACTER: RecursiveCharacterTextSplitter,
        }

    def chunk_text(
        self,
        text: str,
    ) -> list[str]:
        return self.split_text(text)

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
