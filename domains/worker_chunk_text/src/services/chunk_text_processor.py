import json
from typing import Any, ClassVar, Iterator, TypeGuard

from chunking.domain.central_text_splitter import CentralTextSplitter
from configs.chunking_scaffold import ChunkingStage, ChunkingStages
from langchain_core.documents import Document
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.provenance import build_id, chunk_params_hash, sha256_hex
from pipeline_common.stages_contracts import (
    BaseProcessor,
    StageArtifact,
    StageArtifactMetadata,
)

from contracts.contracts import (
    StorageStageArtifact,
    ChunkMetadata,
    ChunkingExecutionResult,
    ProcessResult,
    ProcessorContext,
    SourceDocumentMetadata,
)


class ChunkTextProcessor(BaseProcessor):
    """Transform processed document rows into persisted chunk artifacts.

    The processor handles the full chunking pipeline for a single payload:
    normalize source text into chunk records, write chunk artifacts, and return
    metadata required by downstream manifest assembly.
    """

    VERSION: ClassVar[str] = "1.0.0"
    STAGE_NAME: ClassVar[str] = "chunk_text"
    CHUNKS_DIR: ClassVar[str] = "chunks"

    def __init__(
        self,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        output_prefix: str,
    ) -> None:
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.output_prefix = output_prefix

    def process(
        self,
        *,
        input_artifact: StageArtifact,
        source_uri: str,
        run_id: str,
        stages: ChunkingStages,
    ) -> ProcessResult:
        """Run the golden path once: stage-chain split and persist chunk artifacts."""
        serialized_stages: list[dict[str, Any]] = stages.to_serializable_dict()
        source_metadata: SourceDocumentMetadata = input_artifact.source_metadata
        input_content = input_artifact.content
        processor_context: ProcessorContext = ProcessorContext(
            params_hash=chunk_params_hash(serialized_stages),
            params=serialized_stages,
        )
        docs: list[Document] = self._process_stages(
            source_text=input_content.text,
            stages=stages.stages,
        )
        execution_result: ChunkingExecutionResult = self._write_chunk_artifacts(
            docs=docs,
            serialized_stages=serialized_stages,
            source_uri=source_uri,
            run_id=run_id,
            source_metadata=source_metadata,
        )

        return ProcessResult(
            run_id=run_id,
            source_metadata=source_metadata,
            source_uri=source_uri,
            processor_context=processor_context,
            params=serialized_stages,
            processor=self.processor_metadata,
            result=execution_result,
        )

    def _process_stages(
        self,
        *,
        source_text: str,
        stages: list[ChunkingStage],
    ) -> list[Document]:
        """Apply each LangChain stage sequentially, feeding one stage output into the next.

        Starts from raw source text, then repeatedly splits either:
        - raw text inputs (via `create_documents`), or
        - document inputs from a previous stage (via `split_documents`).
        Returns the final document list.
        """
        docs: list[str] | list[Document] = [source_text]

        for stage in stages:
            splitter = CentralTextSplitter(stage=stage)
            docs = self._apply_stage(
                splitter=splitter,
                docs=docs,
            )
        return docs

    def _apply_stage(
        self,
        *,
        splitter: CentralTextSplitter,
        docs: list[str] | list[Document],
    ) -> list[Document]:
        if self._docs_are_documents(docs):
            return splitter.split_documents(documents=docs)
        texts = [str(item) for item in docs]
        return splitter.create_documents(texts=texts)

    def _docs_are_documents(self, docs: list[str] | list[Document]) -> TypeGuard[list[Document]]:
        return bool(docs) and hasattr(docs[0], "page_content")

    def _write_chunk_artifacts(
        self,
        *,
        docs: list[Document],
        serialized_stages: list[dict[str, Any]],
        source_uri: str,
        run_id: str,
        source_metadata: SourceDocumentMetadata,
    ) -> ChunkingExecutionResult:
        chunk_count_expected = 0
        written = 0
        chunk_entries: list[str] = []

        for storage_stage_artifact in self._build_chunk_artifacts(
            docs=docs,
            serialized_stages=serialized_stages,
            source_uri=source_uri,
            run_id=run_id,
            source_metadata=source_metadata,
        ):
            chunk_count_expected += 1
            chunk_entries.append(storage_stage_artifact.destination_key)
            self._write_chunk_object(storage_stage_artifact)
            written += 1

        return ChunkingExecutionResult(
            chunk_count_expected=chunk_count_expected,
            chunk_count_written=written,
            chunk_entries=chunk_entries,
        )

    def _build_chunk_artifacts(
        self,
        *,
        docs: list[Document],
        serialized_stages: list[dict[str, Any]],
        source_uri: str,
        run_id: str,
        source_metadata: SourceDocumentMetadata,
    ) -> Iterator[StorageStageArtifact]:
        source_metadata_payload = source_metadata.to_dict
        processor_metadata_payload = self.processor_metadata.to_dict

        for chunk_index, doc in enumerate(docs):
            chunk_metadata: ChunkMetadata = self._build_chunk_metadata(
                chunk_index=chunk_index,
                doc=doc,
                source_uri=source_uri,
                source_metadata=source_metadata_payload,
                processor=processor_metadata_payload,
                params=serialized_stages,
            )
            chunk_artifact = StorageStageArtifact(
                artifact=StageArtifact(
                    metadata=StageArtifactMetadata(
                        processor=self.processor_metadata,
                        source=source_metadata,
                        params=serialized_stages,
                        content=chunk_metadata,
                    ),
                    content=doc.page_content,
                ),
                destination_key=self._chunk_object_key(
                    doc_id=source_metadata.doc_id,
                    run_id=run_id,
                    chunk_id=chunk_metadata.chunk_id,
                ),
            )
            yield chunk_artifact

    def _build_chunk_metadata(
        self,
        *,
        chunk_index: int,
        doc: Document,
        source_uri: str,
        source_metadata: dict[str, Any],
        processor: dict[str, Any],
        params: list[dict[str, Any]],
    ) -> ChunkMetadata:
        chunk_text = str(doc.page_content)
        chunk_text_hash = sha256_hex(chunk_text)
        offsets_start = int(doc.metadata.get("start_index", 0))
        offsets_end = offsets_start + len(chunk_text)
        chunk_id = build_id(
            source_uri=source_uri,
            source_metadata=source_metadata,
            processor=processor,
            params=params,
            content={
                "offsets_start": offsets_start,
                "offsets_end": offsets_end,
                "chunk_text_hash": chunk_text_hash,
            },
        )
        chunk_metadata: ChunkMetadata = ChunkMetadata(
            index=chunk_index,
            chunk_id=chunk_id,
            offsets_start=offsets_start,
            offsets_end=offsets_end,
            chunk_text_hash=chunk_text_hash,
        )
        return chunk_metadata

    def _chunk_object_key(self, doc_id: str, run_id: str, chunk_id: str) -> str:
        return (
            f"{self.output_prefix.rstrip('/')}/"
            f"{self.CHUNKS_DIR}/{doc_id}/run={run_id}/chunk={chunk_id}.json"
        )

    def _write_chunk_object(self, chunk_artifact: StorageStageArtifact) -> None:
        self.object_storage.write_object(
            bucket=self.storage_bucket,
            key=chunk_artifact.destination_key,
            payload=json.dumps(
                chunk_artifact.to_payload,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )
