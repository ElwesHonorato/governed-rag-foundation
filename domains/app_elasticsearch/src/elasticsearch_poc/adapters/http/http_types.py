"""Shared HTTP types for the Elasticsearch WSGI app."""

from __future__ import annotations

from typing import Callable


StartResponse = Callable[[str, list[tuple[str, str]]], None]
WsgiEnv = dict[str, object]
JsonValue = dict[str, object] | list[object]
