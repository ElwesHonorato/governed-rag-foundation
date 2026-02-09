from __future__ import annotations

from services.worker_parse_document_service import WorkerParseDocumentService


def run() -> None:
    WorkerParseDocumentService.from_env().run_forever()


if __name__ == "__main__":
    run()
