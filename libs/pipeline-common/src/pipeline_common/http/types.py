"""Shared HTTP types for stdlib WSGI applications."""

from __future__ import annotations

from typing import Callable


StartResponse = Callable[[str, list[tuple[str, str]]], None]
WsgiEnv = dict[str, object]
JsonValue = dict[str, object] | list[object]
