"""Small command index for the standalone Elasticsearch proof of concept."""

from __future__ import annotations


def main() -> int:
    print("Available commands:")
    print("- poetry run elasticsearch-poc-create-index")
    print("- poetry run elasticsearch-poc-seed")
    print("- poetry run elasticsearch-poc-search \"<query>\"")
    print("- poetry run elasticsearch-poc-import-minio")
    print("- poetry run elasticsearch-poc-demo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
