from abc import ABC, abstractmethod

from contracts.contracts import ScanStorageContract


class ScanCycleProcessor(ABC):
    """Contract for one scan cycle execution."""

    @abstractmethod
    def scan(self) -> int:
        """Run one scan cycle and return the number of processed items."""

class StorageScanCycleProcessor(ScanCycleProcessor):
    """Build scan decisions for source->destination promotion."""

    def __init__(
        self,
        *,
        storage_contract: ScanStorageContract,
    ) -> None:
        """Initialize instance state and dependencies."""
        self.bucket = storage_contract.bucket
        self.source_prefix = storage_contract.input_prefix
        self.destination_prefix = storage_contract.output_prefix

    def scan(self) -> int:
        """Compatibility no-op for abstract contract."""
        return 0

    def candidate_keys(self, keys: list[str]) -> list[str]:
        return [key for key in keys if self.is_candidate_key(key)]

    def is_candidate_key(self, key: str) -> bool:
        """Return True when a key is a processable source object."""
        return key.startswith(self.source_prefix) and key != self.source_prefix

    def destination_key(self, source_key: str) -> str:
        """Map a source key to its destination key."""
        return source_key.replace(self.source_prefix, self.destination_prefix, 1)
