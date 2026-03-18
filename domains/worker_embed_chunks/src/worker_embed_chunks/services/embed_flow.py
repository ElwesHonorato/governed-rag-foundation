"""Embed worker orchestration contracts."""

from dataclasses import dataclass

from pipeline_common.stages_contracts import EmbeddingArtifact, EmbeddingArtifactMetadata


@dataclass(frozen=True)
class EmbedWorkItem:
    """One embedding work item derived from an inbound URI."""

    uri: str
