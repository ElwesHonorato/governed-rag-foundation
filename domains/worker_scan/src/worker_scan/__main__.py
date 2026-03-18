"""Module entrypoint for the source scanning worker.

This wrapper supports `python -m worker_scan` and delegates process startup to
`worker_scan.app.main()`. Keeping the execution handoff here leaves `app.py`
focused on composition-root wiring, runtime config extraction, and service
construction.
"""

from worker_scan.app import main


if __name__ == "__main__":
    raise SystemExit(main())
