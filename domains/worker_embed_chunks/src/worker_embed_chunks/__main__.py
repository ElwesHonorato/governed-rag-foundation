"""Module entrypoint for the chunk embedding worker.

This wrapper supports `python -m worker_embed_chunks` and delegates process
startup to `worker_embed_chunks.app.main()`. Keeping the execution handoff here
leaves `app.py` focused on composition-root wiring, runtime config extraction,
and service construction.
"""

from worker_embed_chunks.app import main


if __name__ == "__main__":
    raise SystemExit(main())
