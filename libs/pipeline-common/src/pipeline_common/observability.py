from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Counters:
    files_processed: int = 0
    chunks_created: int = 0
    embedding_artifacts: int = 0
    index_upserts: int = 0
    failures: int = 0
    _worker_name: str = field(default="worker")

    def for_worker(self, worker_name: str) -> "Counters":
        self._worker_name = worker_name
        return self

    def emit(self) -> None:
        print(
            f"[{self._worker_name}] counters "
            f"files_processed={self.files_processed} "
            f"chunks_created={self.chunks_created} "
            f"embedding_artifacts={self.embedding_artifacts} "
            f"index_upserts={self.index_upserts} "
            f"failures={self.failures}",
            flush=True,
        )
