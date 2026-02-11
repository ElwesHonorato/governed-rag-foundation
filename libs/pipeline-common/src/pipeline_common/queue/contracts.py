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


class StageQueueContract(TypedDict):
    consume: str
    produce: str
    dlq: str


WORKER_STAGE_QUEUES: dict[str, StageQueueContract] = {
    "scan": {
        "consume": "",
        "produce": "q.parse_document",
        "dlq": "q.scan.dlq",
    },
    "parse_document": {
        "consume": "q.parse_document",
        "produce": "q.chunk_text",
        "dlq": "q.parse_document.dlq",
    },
    "chunk_text": {
        "consume": "q.chunk_text",
        "produce": "q.embed_chunks",
        "dlq": "q.chunk_text.dlq",
    },
    "embed_chunks": {
        "consume": "q.embed_chunks",
        "produce": "q.index_weaviate",
        "dlq": "q.embed_chunks.dlq",
    },
    "index_weaviate": {
        "consume": "q.index_weaviate",
        "produce": "",
        "dlq": "q.index_weaviate.dlq",
    },
}
