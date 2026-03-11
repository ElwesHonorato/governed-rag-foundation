import time
import logging

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
        poll_interval_seconds: int,
        storage_bucket: str,
        chunks_prefix: str,
        embeddings_prefix: str,
        indexes_prefix: str,
        processed_prefix: str,
        processor: ManifestCycleProcessor,
    ) -> None:
        """Initialize instance state and dependencies."""
        self._storage_gateway = object_storage
        self._lineage_gateway = lineage
        self._poll_interval_seconds = poll_interval_seconds
        self._storage_bucket = storage_bucket
        self._processed_prefix = processed_prefix
        self._chunks_prefix = chunks_prefix
        self._embeddings_prefix = embeddings_prefix
        self._indexes_prefix = indexes_prefix
        self._processor = processor

    def serve(self) -> None:
        """Run the worker loop indefinitely."""
        while True:
            self._run_manifest_iteration()

    def _run_manifest_iteration(self) -> None:
        self._run_manifest_cycle()
        self._sleep_until_next_cycle()

    def _run_manifest_cycle(self) -> None:
        processed_keys = self._storage_gateway.list_keys(self._storage_bucket, self._processed_prefix)
        for doc_id in self._processor.list_doc_ids(processed_keys):
            self._write_manifest_for_doc(doc_id)

    def _write_manifest_for_doc(self, doc_id: str) -> None:
        processed_key = f"{self._processed_prefix}{doc_id}.json"
        manifest_key = self._processor.build_manifest_key(doc_id)
        self._register_lineage_io(processed_key=processed_key, manifest_key=manifest_key)
        try:
            chunks_prefix = f"{self._chunks_prefix}{doc_id}"
            embeddings_prefix = f"{self._embeddings_prefix}{doc_id}"
            indexes_prefix = f"{self._indexes_prefix}{doc_id}"
            status_body = self._processor.build_manifest_status(
                doc_id=doc_id,
                parse_document=self._storage_gateway.object_exists(self._storage_bucket, processed_key),
                chunk_text=self._processor.any_stage_object_exists(
                    self._storage_gateway.list_keys(self._storage_bucket, chunks_prefix),
                    chunks_prefix,
                    (".chunk.json", ".chunks.json"),
                ),
                embed_chunks=self._processor.any_stage_object_exists(
                    self._storage_gateway.list_keys(self._storage_bucket, embeddings_prefix),
                    embeddings_prefix,
                    (".embedding.json", ".embeddings.json"),
                ),
                index_weaviate=self._processor.any_stage_object_exists(
                    self._storage_gateway.list_keys(self._storage_bucket, indexes_prefix),
                    indexes_prefix,
                    (".indexed.json",),
                ),
            )
            self._storage_gateway.write_object(
                self._storage_bucket,
                manifest_key,
                status_body,
                content_type="application/json",
            )
            self._lineage_gateway.complete_run()
        except Exception as exc:
            self._lineage_gateway.fail_run(error_message=str(exc))
            logger.exception("Failed writing manifest for doc_id '%s'", doc_id)
            raise

    def _register_lineage_io(self, *, processed_key: str, manifest_key: str) -> None:
        self._lineage_gateway.start_run()
        self._lineage_gateway.add_input(
            name=f"{self._storage_bucket}/{processed_key}",
            platform=DatasetPlatform.S3,
        )
        self._lineage_gateway.add_output(
            name=f"{self._storage_bucket}/{manifest_key}",
            platform=DatasetPlatform.S3,
        )

    def _sleep_until_next_cycle(self) -> None:
        time.sleep(self._poll_interval_seconds)
