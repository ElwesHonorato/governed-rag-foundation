"""Startup wiring helpers for worker_chunk_text."""

from startup.config_extractor import ChunkTextConfigExtractor
from startup.service_factory import ChunkTextServiceFactory

__all__ = ["ChunkTextConfigExtractor", "ChunkTextServiceFactory"]
