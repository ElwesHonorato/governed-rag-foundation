from abc import ABC, abstractmethod


class CycleProcessor(ABC):
    @abstractmethod
    def scan(self) -> int:
        """Run one scan cycle and return the number of processed items."""
