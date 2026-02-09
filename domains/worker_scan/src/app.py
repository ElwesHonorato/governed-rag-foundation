from __future__ import annotations

from services.worker_scan_service import WorkerScanService


def run() -> None:
    WorkerScanService.from_env().run_forever()


if __name__ == "__main__":
    run()
