from __future__ import annotations

from services.worker_manifest_service import WorkerManifestService


def run() -> None:
    WorkerManifestService.from_env().run_forever()


if __name__ == "__main__":
    run()
