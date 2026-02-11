from typing import TypedDict


class QueueStorageKeyMessage(TypedDict):
    storage_key: str


class ParseDocumentFailed(TypedDict):
    storage_key: str
    doc_id: str
    error: str
    failed_at: str


class IndexWeaviateRequested(TypedDict):
    embeddings_key: str
    doc_id: str
