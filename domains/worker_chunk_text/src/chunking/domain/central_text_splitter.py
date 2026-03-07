"""Central wrapper for text splitter configuration."""

from typing import Any

class CentralTextSplitter:
    """Single entrypoint for chunk splitter creation and usage."""

    def __init__(self, *, chunker: type[Any], params: dict[str, Any]) -> None:
        self._splitter = self._build_splitter(chunker=chunker, params=params)

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
