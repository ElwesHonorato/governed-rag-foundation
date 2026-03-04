"""Spark runtime session helpers.

This module keeps ``pyspark`` as an optional dependency. Non-Spark workers
must be able to import startup/runtime modules even when ``pyspark`` is not
installed. To preserve that behavior, ``pyspark`` is imported lazily only when
``build_spark_session`` is called.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


def build_spark_session(*, app_name: str, master_url: str) -> Any:
    """Build one SparkSession with lazy ``pyspark`` loading.

    ``pyspark`` import happens at call time (not module import time) so workers
    running with ``spark=False`` never fail due to missing Spark dependencies.
    """
    try:
        spark_sql = import_module("pyspark.sql")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Spark session requested but pyspark is not installed in this runtime."
        ) from exc

    spark_session_cls = getattr(spark_sql, "SparkSession")
    return (
        spark_session_cls.builder
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
