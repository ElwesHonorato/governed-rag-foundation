
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_text(text: str, target_size: int = 700, overlap: int = 120) -> list[str]:
    """Split text using LangChain recursive character chunking."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=target_size,
        chunk_overlap=overlap,
    )
    return [chunk for chunk in splitter.split_text(text) if chunk.strip()]
