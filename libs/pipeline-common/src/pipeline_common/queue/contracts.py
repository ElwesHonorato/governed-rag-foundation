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
    queue_name: str
    queue_contract: type


class WorkerStageQueueContract(TypedDict):
    consume: StageQueueContract
    produce: StageQueueContract
    dlq: StageQueueContract


QUEUE_MESSAGE_CONTRACTS: dict[str, type] = {
    "q.parse_document": QueueStorageKeyMessage,
    "q.chunk_text": QueueStorageKeyMessage,
    "q.embed_chunks": QueueStorageKeyMessage,
    "q.index_weaviate": IndexWeaviateRequested,
    "q.scan.dlq": QueueStorageKeyMessage,
    "q.parse_document.dlq": ParseDocumentFailed,
    "q.chunk_text.dlq": QueueStorageKeyMessage,
    "q.embed_chunks.dlq": QueueStorageKeyMessage,
    "q.index_weaviate.dlq": IndexWeaviateRequested,
}


WORKER_STAGE_QUEUES: dict[str, WorkerStageQueueContract] = {
    "scan": {
        "consume": {"queue_name": "", "queue_contract": dict},
        "produce": {
            "queue_name": "q.parse_document",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.parse_document"],
        },
        "dlq": {
            "queue_name": "q.scan.dlq",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.scan.dlq"],
        },
    },
    "parse_document": {
        "consume": {
            "queue_name": "q.parse_document",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.parse_document"],
        },
        "produce": {
            "queue_name": "q.chunk_text",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.chunk_text"],
        },
        "dlq": {
            "queue_name": "q.parse_document.dlq",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.parse_document.dlq"],
        },
    },
    "chunk_text": {
        "consume": {
            "queue_name": "q.chunk_text",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.chunk_text"],
        },
        "produce": {
            "queue_name": "q.embed_chunks",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.embed_chunks"],
        },
        "dlq": {
            "queue_name": "q.chunk_text.dlq",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.chunk_text.dlq"],
        },
    },
    "embed_chunks": {
        "consume": {
            "queue_name": "q.embed_chunks",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.embed_chunks"],
        },
        "produce": {
            "queue_name": "q.index_weaviate",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.index_weaviate"],
        },
        "dlq": {
            "queue_name": "q.embed_chunks.dlq",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.embed_chunks.dlq"],
        },
    },
    "index_weaviate": {
        "consume": {
            "queue_name": "q.index_weaviate",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.index_weaviate"],
        },
        "produce": {"queue_name": "", "queue_contract": dict},
        "dlq": {
            "queue_name": "q.index_weaviate.dlq",
            "queue_contract": QUEUE_MESSAGE_CONTRACTS["q.index_weaviate.dlq"],
        },
    },
}
