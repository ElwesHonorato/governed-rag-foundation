"""Chunking strategy registry for worker_chunk_text."""

from langchain_text_splitters import RecursiveCharacterTextSplitter


CHUNKING_STRATEGIES = {
    "STRATEGY_001": {
        "chunker": RecursiveCharacterTextSplitter,
        "params": {
            "strategy": "recursive_character",
            "chunk_size": 700,
            "chunk_overlap": 120,
            "add_start_index": True,
        },
    },
}
