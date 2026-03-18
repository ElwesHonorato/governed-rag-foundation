"""Module entrypoint for the document parsing worker.

This wrapper supports `python -m worker_parse_document` and delegates process
startup to `worker_parse_document.app.main()`. Keeping the execution handoff
here leaves `app.py` focused on composition-root wiring, runtime config
extraction, and service construction.
"""

from worker_parse_document.app import main


if __name__ == "__main__":
    raise SystemExit(main())
