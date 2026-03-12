"""Storage config builder for worker_chunk_text startup."""

from dataclasses import dataclass

from contracts.contracts import RuntimeStoragePathsContract


@dataclass(frozen=True)
class EnvStorageConfigBuilder:
    env: str | None
    storage_config: RuntimeStoragePathsContract

    def build(self) -> RuntimeStoragePathsContract:
        return RuntimeStoragePathsContract(
            bucket=self.storage_config.bucket,
            output_prefix=f"{self.env}/{self.storage_config.output_prefix}",
            manifest_prefix=f"{self.env}/{self.storage_config.manifest_prefix}",
        )
