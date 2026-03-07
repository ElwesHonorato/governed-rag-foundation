"""Central wrapper for recursive text splitting configuration."""

from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter


class CentralTextSplitter:
    """Single entrypoint for recursive chunk splitter creation and usage."""

    def __init__(
        self,
        *,
        chunk_size: int,
        chunk_overlap: int,
        add_start_index: bool = False,
    ) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            add_start_index=add_start_index,
        )

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
