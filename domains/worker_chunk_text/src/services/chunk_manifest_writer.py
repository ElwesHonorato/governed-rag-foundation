import json
from typing import ClassVar

from contracts.contracts import ProcessResult
from pipeline_common.gateways.object_storage import ObjectStorageGateway


class ChunkManifestWriter:
    MANIFEST_FILE_NAME: ClassVar[str] = "manifest.json"
    MANIFEST_OBJECT_KEY_PATTERN: ClassVar[str] = "{doc_id}/runs/{run_id}/{file_name}"

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
        manifest_uri = self.object_storage.build_uri(self.storage_bucket, manifest_key)
        self.object_storage.write_object(
            uri=manifest_uri,
            payload=json.dumps(
                process_result.to_dict,
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )
        self.manifest_uri = manifest_uri

    def _manifest_object_key(self, doc_id: str, run_id: str) -> str:
        return self.MANIFEST_OBJECT_KEY_PATTERN.format(
            doc_id=doc_id,
            run_id=run_id,
            file_name=self.MANIFEST_FILE_NAME,
        )
