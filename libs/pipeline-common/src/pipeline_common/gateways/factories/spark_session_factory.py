"""Spark session factory for worker runtime."""

from typing import Any

from pipeline_common.gateways.processing_engine import build_spark_session
from pipeline_common.settings import SparkSettings


class SparkSessionFactory:
    """Create Spark session from spark settings and composition-root app name."""

    def __init__(self, *, spark_settings: SparkSettings, app_name: str) -> None:
        self.spark_settings = spark_settings
        self.app_name = app_name

    def build(self) -> Any:
        """Create Spark session from required spark settings."""
        return build_spark_session(
            app_name=self.app_name,
            master_url=self.spark_settings.master_url,
        )
