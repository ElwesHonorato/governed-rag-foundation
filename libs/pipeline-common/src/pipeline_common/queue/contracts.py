from typing import TypedDict


class QueueStorageKeyMessage(TypedDict):
    """QueueStorageKeyMessage type definition."""
    storage_key: str


class ParseDocumentFailed(TypedDict):
    """ParseDocumentFailed type definition."""
    storage_key: str
    doc_id: str
    error: str
    failed_at: str


class IndexWeaviateRequested(TypedDict):
    """IndexWeaviateRequested type definition."""
    embeddings_key: str
    doc_id: str

