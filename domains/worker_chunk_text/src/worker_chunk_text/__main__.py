"""Module entrypoint for the text chunking worker.

This wrapper supports `python -m worker_chunk_text` and delegates process startup
to `worker_chunk_text.app.main()`. Keeping the execution handoff here leaves
`app.py` focused on composition-root wiring, runtime config extraction, and
service construction.
"""

from worker_chunk_text.app import main


if __name__ == "__main__":
    raise SystemExit(main())
