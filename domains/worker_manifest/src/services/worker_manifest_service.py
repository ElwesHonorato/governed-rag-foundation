import time
import logging

from contracts.contracts import ManifestProcessingConfigContract
from pipeline_common.gateways.lineage import DatasetPlatform
from pipeline_common.gateways.lineage import LineageRuntimeGateway
from pipeline_common.gateways.object_storage import ObjectStorageGateway
from pipeline_common.startup.contracts import WorkerService
from services.manifest_cycle_processor import ManifestCycleProcessor

logger = logging.getLogger(__name__)


class WorkerManifestService(WorkerService):
    """Build and write per-document manifest status artifacts."""
    def __init__(
        self,
        *,
        object_storage: ObjectStorageGateway,
        lineage: LineageRuntimeGateway,
        processing_config: ManifestProcessingConfigContract,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.object_storage = object_storage
        self.lineage = lineage
        self._initialize_runtime_config(processing_config)
        self.processor = ManifestCycleProcessor(
            processed_prefix=self.processed_prefix,
            manifest_prefix=self.manifest_prefix,
        )

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            self._run_manifest_iteration()

    def _run_manifest_iteration(self) -> None:
        self._run_manifest_cycle()
        self._sleep_until_next_cycle()

    def _run_manifest_cycle(self) -> None:
        processed_keys = self.object_storage.list_keys(self.storage_bucket, self.processed_prefix)
        for doc_id in self.processor.list_doc_ids(processed_keys):
            self._write_manifest_for_doc(doc_id)

    def _write_manifest_for_doc(self, doc_id: str) -> None:
        processed_key = f"{self.processed_prefix}{doc_id}.json"
        manifest_key = self.processor.build_manifest_key(doc_id)
        self.lineage.start_run()
        self.lineage.add_input(
            name=f"{self.storage_bucket}/{processed_key}",
            platform=DatasetPlatform.S3,
        )
        self.lineage.add_output(
            name=f"{self.storage_bucket}/{manifest_key}",
            platform=DatasetPlatform.S3,
        )
        try:
            chunks_prefix = f"{self.chunks_prefix}{doc_id}"
            embeddings_prefix = f"{self.embeddings_prefix}{doc_id}"
            indexes_prefix = f"{self.indexes_prefix}{doc_id}"
            status_body = self.processor.build_manifest_status(
                doc_id=doc_id,
                parse_document=self.object_storage.object_exists(self.storage_bucket, processed_key),
                chunk_text=self.processor.any_stage_object_exists(
                    self.object_storage.list_keys(self.storage_bucket, chunks_prefix),
                    chunks_prefix,
                    (".chunk.json", ".chunks.json"),
                ),
                embed_chunks=self.processor.any_stage_object_exists(
                    self.object_storage.list_keys(self.storage_bucket, embeddings_prefix),
                    embeddings_prefix,
                    (".embedding.json", ".embeddings.json"),
                ),
                index_weaviate=self.processor.any_stage_object_exists(
                    self.object_storage.list_keys(self.storage_bucket, indexes_prefix),
                    indexes_prefix,
                    (".indexed.json",),
                ),
            )
            self.object_storage.write_object(
                self.storage_bucket,
                manifest_key,
                status_body,
                content_type="application/json",
            )
            self.lineage.complete_run()
        except Exception as exc:
            self.lineage.fail_run(error_message=str(exc))
            logger.exception("Failed writing manifest for doc_id '%s'", doc_id)
            raise

    def _sleep_until_next_cycle(self) -> None:
        time.sleep(self.poll_interval_seconds)

    def _initialize_runtime_config(self, processing_config: ManifestProcessingConfigContract) -> None:
        """Internal helper for initialize runtime config."""
        self.poll_interval_seconds = processing_config.poll_interval_seconds
        self.storage_bucket = processing_config.storage.bucket
        self.processed_prefix = processing_config.storage.processed_prefix
        self.chunks_prefix = processing_config.storage.chunks_prefix
        self.embeddings_prefix = processing_config.storage.embeddings_prefix
        self.indexes_prefix = processing_config.storage.indexes_prefix
        self.manifest_prefix = processing_config.storage.manifest_prefix
