import json
from typing import ClassVar

from contracts.contracts import ProcessResult
from pipeline_common.gateways.object_storage import ObjectStorageGateway


class ChunkManifestWriter:
    STAGE_NAME: ClassVar[str] = "chunks_manifest"
    MANIFEST_FILE_NAME: ClassVar[str] = "manifest.json"
    MANIFEST_OBJECT_KEY_PATTERN: ClassVar[str] = "{stage_name}/{dir}/{doc_id}/run={run_id}/{file_name}"

    def __init__(
        self,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        manifest_prefix: str,
    ) -> None:
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.manifest_prefix = manifest_prefix
        self.manifest_uri: str | None = None

    def write(self, *, process_result: ProcessResult) -> None:
        source_metadata = process_result.source_metadata
        manifest_key = self._manifest_object_key(doc_id=source_metadata.doc_id, run_id=process_result.run_id)
        self.object_storage.write_object(
            self.storage_bucket,
            manifest_key,
            json.dumps(
                process_result.to_dict,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )
        self.manifest_uri = f"s3a://{self.storage_bucket}/{manifest_key}"

    def _manifest_object_key(self, doc_id: str, run_id: str) -> str:
        return self.MANIFEST_OBJECT_KEY_PATTERN.format(
            stage_name=self.manifest_prefix.rstrip("/"),
            dir=self.STAGE_NAME,
            doc_id=doc_id,
            run_id=run_id,
            file_name=self.MANIFEST_FILE_NAME,
        )
