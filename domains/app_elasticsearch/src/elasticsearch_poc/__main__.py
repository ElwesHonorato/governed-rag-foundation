"""Module entrypoint for the Elasticsearch app domain.

This wrapper supports `python -m elasticsearch_poc` and delegates execution to
`elasticsearch_poc.app.main()`. Keeping the execution handoff here leaves
`app.py` focused on the command index for this domain.
"""

from elasticsearch_poc.app import main


if __name__ == "__main__":
    raise SystemExit(main())
