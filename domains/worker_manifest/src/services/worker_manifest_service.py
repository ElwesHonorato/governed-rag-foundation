import json
import logging
import time

from contracts.contracts import ManifestProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import DataHubRuntimeLineage
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.startup.contracts import WorkerService

logger = logging.getLogger(__name__)


class WorkerManifestService(WorkerService):
    """Build and write per-document manifest status artifacts."""
    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        lineage: DataHubRuntimeLineage,
        processing_config: ManifestProcessingConfigContract,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.object_storage = object_storage
        self.lineage = lineage
        self._initialize_runtime_config(processing_config)

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            processed_keys = [
                key
                for key in self.object_storage.list_keys(self.storage_bucket, self.processed_prefix)
                if key != self.processed_prefix and key.endswith(".json")
            ]

            for processed_key in processed_keys:
                doc_id = processed_key.split("/")[-1].replace(".json", "")
                manifest_key = f"{self.manifest_prefix}{doc_id}.json"
                self._write_manifest_for_doc(doc_id=doc_id, processed_key=processed_key, manifest_key=manifest_key)

            time.sleep(self.poll_interval_seconds)

    def _write_manifest_for_doc(self, *, doc_id: str, processed_key: str, manifest_key: str) -> None:
        """Write one manifest artifact and emit runtime lineage for the write."""
        self.lineage.start_run()
        self.lineage.add_input(name=f"{self.storage_bucket}/{processed_key}", platform=DatasetPlatform.S3)
        self.lineage.add_output(name=f"{self.storage_bucket}/{manifest_key}", platform=DatasetPlatform.S3)
        try:
            status = {
                "doc_id": doc_id,
                "stages": {
                    "parse_document": self.object_storage.object_exists(
                        self.storage_bucket, f"{self.processed_prefix}{doc_id}.json"
                    ),
                    "chunk_text": self._any_stage_object_exists(
                        self.chunks_prefix,
                        doc_id,
                        (".chunk.json", ".chunks.json"),
                    ),
                    "embed_chunks": self._any_stage_object_exists(
                        self.embeddings_prefix,
                        doc_id,
                        (".embedding.json", ".embeddings.json"),
                    ),
                    "index_weaviate": self._any_stage_object_exists(
                        self.indexes_prefix,
                        doc_id,
                        (".indexed.json",),
                    ),
                },
                "attempts": 1,
                "last_error": None,
            }
            self.object_storage.write_object(
                self.storage_bucket,
                manifest_key,
                json.dumps(status, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8"),
                content_type="application/json",
            )
            self.lineage.complete_run()
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            logger.exception("Failed writing manifest for doc_id '%s'", doc_id)
            raise

    def _any_stage_object_exists(self, stage_prefix: str, doc_id: str, suffixes: tuple[str, ...]) -> bool:
        """Return whether any stage object exists for the document id."""
        doc_prefix = f"{stage_prefix}{doc_id}"
        stage_keys = self.object_storage.list_keys(self.storage_bucket, doc_prefix)
        return any(key != doc_prefix and key.endswith(suffixes) for key in stage_keys)

    def _initialize_runtime_config(self, processing_config: ManifestProcessingConfigContract) -> None:
        """Internal helper for initialize runtime config."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.processed_prefix = processing_config.storage.processed_prefix
        self.chunks_prefix = processing_config.storage.chunks_prefix
        self.embeddings_prefix = processing_config.storage.embeddings_prefix
        self.indexes_prefix = processing_config.storage.indexes_prefix
        self.manifest_prefix = processing_config.storage.manifest_prefix
