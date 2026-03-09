import json
from typing import Mapping

from pipeline_common.gateways.object_storage import ObjectStorageGateway


class ChunkManifestWriter:
    CHUNKS_MANIFEST_DIR = "chunks_manifest"
    MANIFEST_FILE_NAME = "manifest.json"

    def __init__(
        self,
        object_storage: ObjectStorageGateway,
        storage_bucket: str,
        manifest_prefix: str,
    ) -> None:
        self.object_storage = object_storage
        self.storage_bucket = storage_bucket
        self.manifest_prefix = manifest_prefix

    def write(self, *, manifest: Mapping[str, object], doc_id: str, run_id: str) -> None:
        self.object_storage.write_object(
            self.storage_bucket,
            self._manifest_object_key(doc_id=doc_id, run_id=run_id),
            json.dumps(
                dict(manifest),
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
            ).encode("utf-8"),
            content_type="application/json",
        )

    def _manifest_object_key(self, doc_id: str, run_id: str) -> str:
        return (
            f"{self.manifest_prefix.rstrip('/')}/"
            f"{self.CHUNKS_MANIFEST_DIR}/{doc_id}/run={run_id}/"
            f"{self.MANIFEST_FILE_NAME}"
        )
