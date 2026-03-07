"""Central wrapper for recursive text splitting configuration."""

from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter


class CentralTextSplitter:
    """Single entrypoint for recursive chunk splitter creation and usage."""

    def __init__(
        self,
        *,
        chunker: type[RecursiveCharacterTextSplitter],
        params: dict[str, Any],
    ) -> None:
        self._splitter = self._build_splitter(
            chunker=chunker,
            params=params,
        )

    def _build_splitter(
        self,
        *,
        chunker: type[RecursiveCharacterTextSplitter],
        params: dict[str, Any],
    ) -> RecursiveCharacterTextSplitter:
        return chunker(**params)

    def create_documents(self, **kwargs: Any) -> list[Any]:
        """Create LangChain documents from source texts."""
        return self._splitter.create_documents(**kwargs)
