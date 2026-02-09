from __future__ import annotations

from services.worker_embed_chunks_service import WorkerEmbedChunksService


def run() -> None:
    WorkerEmbedChunksService.from_env().run_forever()


if __name__ == "__main__":
    run()
