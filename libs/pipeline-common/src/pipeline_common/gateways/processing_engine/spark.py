"""Spark runtime session helpers."""

from __future__ import annotations

from typing import Any


def build_spark_session(*, enabled: bool, app_name: str, master_url: str) -> Any | None:
    """Build one SparkSession when enabled, otherwise return None."""
    if not enabled:
        return None
    try:
        from pyspark.sql import SparkSession  # type: ignore
    except ImportError as exc:
        raise RuntimeError("pyspark is required when SPARK_ENABLED=true") from exc
    return (
        SparkSession.builder
        .appName(app_name)
        .master(master_url)
        .getOrCreate()
    )


def stop_spark_session(spark_session: Any | None) -> None:
    """Stop an existing SparkSession safely."""
    if spark_session is None:
        return
    try:
        spark_session.stop()
    except Exception:
        pass
