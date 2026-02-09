from __future__ import annotations

from services.worker_chunk_text_service import WorkerChunkTextService


def run() -> None:
    WorkerChunkTextService.from_env().run_forever()


if __name__ == "__main__":
    run()
