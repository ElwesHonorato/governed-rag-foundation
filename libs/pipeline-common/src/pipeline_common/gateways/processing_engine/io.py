"""Dataframe read/write gateway abstractions."""

from __future__ import annotations

from typing import Any, Protocol


class DataframeReadGateway(Protocol):
    """Read-side dataframe abstraction used by worker processors."""

    def read(self, *, path: str, format_name: str) -> Any:
        """Read a DataFrame using any supported format."""

    def from_records(self, records: list[dict[str, Any]]) -> Any:
        """Build a DataFrame from in-memory records."""


class DataframeWriteGateway(Protocol):
    """Write-side dataframe abstraction used by worker processors."""

    def write(
        self,
        dataframe: Any,
        *,
        path: str,
        format_name: str,
        mode: str = "error",
    ) -> None:
        """Write a DataFrame."""


class ReadGateway:
    """Concrete read gateway backed by a dataframe session instance."""

    def __init__(self, *, session: Any) -> None:
        self._session = session

    def read(self, *, path: str, format_name: str) -> Any:
        """Read a DataFrame via session reader."""
        return self._session.read.format(format_name).load(path)

    def from_records(self, records: list[dict[str, Any]]) -> Any:
        """Build a DataFrame via session createDataFrame."""
        return self._session.createDataFrame(records)


class WriteGateway:
    """Concrete write gateway backed by dataframe writers."""

    def write(
        self,
        dataframe: Any,
        *,
        path: str,
        format_name: str,
        mode: str = "error",
    ) -> None:
        """Write DataFrame using the requested writer format."""
        dataframe.write.mode(mode).format(format_name).save(path)
