from __future__ import annotations

from services.worker_index_weaviate_service import WorkerIndexWeaviateService


def run() -> None:
    WorkerIndexWeaviateService.from_env().run_forever()


if __name__ == "__main__":
    run()
