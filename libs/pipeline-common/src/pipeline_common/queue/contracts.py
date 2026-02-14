from dataclasses import dataclass

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


class StageQueueContract(TypedDict):
    """StageQueueContract type definition."""
    queue_name: str
    queue_contract: type


class WorkerStageQueueContract(TypedDict):
    """WorkerStageQueueContract type definition."""
    consume: StageQueueContract
    produce: StageQueueContract
    dlq: StageQueueContract


@dataclass(frozen=True)
class QueueDef:
    """QueueDef type definition."""
    name: str
    contract: type


QUEUE_DEFINITIONS = {
    "parse_document": QueueDef("q.parse_document", QueueStorageKeyMessage),
    "chunk_text": QueueDef("q.chunk_text", QueueStorageKeyMessage),
    "embed_chunks": QueueDef("q.embed_chunks", QueueStorageKeyMessage),
    "index_weaviate": QueueDef("q.index_weaviate", IndexWeaviateRequested),
    "scan_dlq": QueueDef("q.scan.dlq", QueueStorageKeyMessage),
    "parse_document_dlq": QueueDef("q.parse_document.dlq", ParseDocumentFailed),
    "chunk_text_dlq": QueueDef("q.chunk_text.dlq", QueueStorageKeyMessage),
    "embed_chunks_dlq": QueueDef("q.embed_chunks.dlq", QueueStorageKeyMessage),
    "index_weaviate_dlq": QueueDef("q.index_weaviate.dlq", IndexWeaviateRequested),
}


def queue_contract_for(q: QueueDef) -> StageQueueContract:
    """Execute queue contract for."""
    return {"queue_name": q.name, "queue_contract": q.contract}


NO_QUEUE: StageQueueContract = {"queue_name": "", "queue_contract": dict}


WORKER_STAGE_QUEUES: dict[str, WorkerStageQueueContract] = {
    "scan": {
        "consume": NO_QUEUE,
        "produce": queue_contract_for(QUEUE_DEFINITIONS["parse_document"]),
        "dlq": queue_contract_for(QUEUE_DEFINITIONS["scan_dlq"]),
    },
    "parse_document": {
        "consume": queue_contract_for(QUEUE_DEFINITIONS["parse_document"]),
        "produce": queue_contract_for(QUEUE_DEFINITIONS["chunk_text"]),
        "dlq": queue_contract_for(QUEUE_DEFINITIONS["parse_document_dlq"]),
    },
    "chunk_text": {
        "consume": queue_contract_for(QUEUE_DEFINITIONS["chunk_text"]),
        "produce": queue_contract_for(QUEUE_DEFINITIONS["embed_chunks"]),
        "dlq": queue_contract_for(QUEUE_DEFINITIONS["chunk_text_dlq"]),
    },
    "embed_chunks": {
        "consume": queue_contract_for(QUEUE_DEFINITIONS["embed_chunks"]),
        "produce": queue_contract_for(QUEUE_DEFINITIONS["index_weaviate"]),
        "dlq": queue_contract_for(QUEUE_DEFINITIONS["embed_chunks_dlq"]),
    },
    "index_weaviate": {
        "consume": queue_contract_for(QUEUE_DEFINITIONS["index_weaviate"]),
        "produce": NO_QUEUE,
        "dlq": queue_contract_for(QUEUE_DEFINITIONS["index_weaviate_dlq"]),
    },
}
