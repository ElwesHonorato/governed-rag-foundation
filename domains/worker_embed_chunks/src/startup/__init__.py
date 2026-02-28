"""Startup wiring helpers for worker_embed_chunks."""

from startup.config_extractor import EmbedChunksConfigExtractor
from startup.service_factory import EmbedChunksServiceFactory

__all__ = ["EmbedChunksConfigExtractor", "EmbedChunksServiceFactory"]
