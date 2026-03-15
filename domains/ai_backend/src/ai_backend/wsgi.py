"""WSGI module-level application for server imports."""

from __future__ import annotations

from ai_backend.app_factory import create_app


app = create_app()
