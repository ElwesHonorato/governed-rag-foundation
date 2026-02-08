from __future__ import annotations

import time

from pipeline_worker.config import Settings
from pipeline_worker.s3_workspace import WorkspaceBootstrap


def run() -> None:
    settings = Settings()
    WorkspaceBootstrap(settings).bootstrap()

    while True:
        time.sleep(30)


if __name__ == "__main__":
    run()
