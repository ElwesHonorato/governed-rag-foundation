"""Module entrypoint for the Weaviate indexing worker.

This wrapper supports `python -m worker_index_weaviate` and delegates process
startup to `worker_index_weaviate.app.main()`. Keeping the execution handoff
here leaves `app.py` focused on composition-root wiring, runtime config
extraction, and service construction.
"""

from worker_index_weaviate.app import main


if __name__ == "__main__":
    raise SystemExit(main())
