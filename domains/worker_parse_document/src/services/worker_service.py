from abc import ABC, abstractmethod


class WorkerService(ABC):
    @abstractmethod
    def run_forever(self) -> None:
        """Run the worker loop indefinitely."""
