"""Thin wrapper around LangChain splitters selected by chunking stages."""

from dataclasses import asdict
from typing import Any

from worker_chunk_text.chunking.stage_contract import ChunkingStage
from langchain_core.documents import Document


class StageSplitter:
    """Instantiate and delegate to the splitter configured for one stage."""

    def __init__(self, *, stage: ChunkingStage) -> None:
        """Build the underlying splitter instance for a single chunking stage."""
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
        """Instantiate a splitter implementation with serialized dataclass params."""
        return chunker(**params)

    def create_documents(self, **kwargs: Any) -> list[Document]:
        """Delegate ``create_documents`` to the configured LangChain splitter."""
        return self._splitter.create_documents(**kwargs)

    def split_documents(self, **kwargs: Any) -> list[Document]:
        """Delegate ``split_documents`` to the configured LangChain splitter."""
        return self._splitter.split_documents(**kwargs)
