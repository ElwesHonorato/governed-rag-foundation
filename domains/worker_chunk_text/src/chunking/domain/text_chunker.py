
from chunking.domain.central_text_splitter import CentralTextSplitter


def chunk_text(text: str, target_size: int = 700, overlap: int = 120) -> list[str]:
    """Split text using LangChain recursive character chunking."""
    splitter = CentralTextSplitter(
        chunk_size=target_size,
        chunk_overlap=overlap,
    )
    return splitter.split_text(text)
