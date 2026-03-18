"""Module entrypoint for the vector UI service.

Supports `python -m vector_ui` while keeping startup wiring in `app.py`.
"""

from vector_ui.app import main


if __name__ == "__main__":
    raise SystemExit(main())
