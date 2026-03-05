"""PySpark read/write gateway abstractions.

This module adds explicit read and write abstractions on top of an existing
SparkSession. Worker processors can migrate from direct ``SparkSession`` calls
to these gateways incrementally.
"""

from __future__ import annotations

from typing import Any, Protocol


class SparkReadGateway(Protocol):
    """Read-side Spark abstraction used by worker processors."""

    def read(self, *, path: str, format_name: str) -> Any:
        """Read a DataFrame using any Spark-supported format."""

    def from_records(self, records: list[dict[str, Any]]) -> Any:
        """Build a DataFrame from in-memory records."""


class SparkWriteGateway(Protocol):
    """Write-side Spark abstraction used by worker processors."""

    def write(
        self,
        dataframe: Any,
        *,
        path: str,
        format_name: str,
        mode: str = "error",
    ) -> None:
        """Write a DataFrame using distributed Spark writers."""


class ReadGateway:
    """Concrete read gateway backed by a SparkSession instance."""

    def __init__(self, *, spark_session: Any) -> None:
        self._spark_session = spark_session

    def read(self, *, path: str, format_name: str) -> Any:
        """Read a DataFrame via Spark distributed reader."""
        return self._spark_session.read.format(format_name).load(path)

    def from_records(self, records: list[dict[str, Any]]) -> Any:
        """Build a DataFrame via SparkSession.createDataFrame."""
        return self._spark_session.createDataFrame(records)


class WriteGateway:
    """Concrete write gateway backed by Spark distributed DataFrame writers."""

    def write(
        self,
        dataframe: Any,
        *,
        path: str,
        format_name: str,
        mode: str = "error",
    ) -> None:
        """Write DataFrame using any Spark-supported distributed writer format."""
        dataframe.write.mode(mode).format(format_name).save(path)
