from __future__ import annotations

from services.worker_metrics_service import WorkerMetricsService


def run() -> None:
    WorkerMetricsService.from_env().run_forever()


if __name__ == "__main__":
    run()
