
from chunking.domain.central_text_splitter import CentralTextSplitter
from contracts.contracts import ChunkingParamsContract
from contracts.chunking_strategy import ChunkingStrategy


def chunk_text(
    text: str,
    target_size: int = 700,
    overlap: int = 120,
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE_CHARACTER,
) -> list[str]:
    """Split text using LangChain recursive character chunking."""
    splitter = CentralTextSplitter(
        chunking_params=ChunkingParamsContract(
            chunk_method=strategy,
            strategy=strategy.value,
            chunk_size=target_size,
            chunk_overlap=overlap,
        ),
    )
    return splitter.chunk_text(text)
