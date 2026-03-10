import json

from contracts.contracts import ProcessResult
from pipeline_common.gateways.object_storage import ObjectStorageGateway


class ChunkManifestWriter:
    STAGE_NAME = "chunks_manifest"
    MANIFEST_FILE_NAME = "manifest.json"
    MANIFEST_OBJECT_KEY_PATTERN = "{stage_name}/{dir}/{doc_id}/run={run_id}/{file_name}"

    def __init__(
        self,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        manifest_prefix: str,
    ) -> None:
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.manifest_prefix = manifest_prefix

    def write(self, *, process_result: ProcessResult) -> None:
        source_metadata = process_result.source_metadata
        self.object_storage.write_object(
            self.storage_bucket,
            self._manifest_object_key(doc_id=source_metadata.doc_id, run_id=process_result.run_id),
            json.dumps(
                process_result.to_dict,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )

    def _manifest_object_key(self, doc_id: str, run_id: str) -> str:
        return self.MANIFEST_OBJECT_KEY_PATTERN.format(
            stage_name=self.manifest_prefix.rstrip("/"),
            dir=self.STAGE_NAME,
            doc_id=doc_id,
            run_id=run_id,
            file_name=self.MANIFEST_FILE_NAME,
        )
