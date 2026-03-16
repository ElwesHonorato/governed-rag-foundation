"""Checkpoint store boundary."""

from __future__ import annotations

from typing import Protocol

from ai_infra.contracts.session_checkpoint import SessionCheckpoint


class CheckpointManager(Protocol):
    """Persistence boundary for checkpoints."""

    def save_checkpoint(self, checkpoint: SessionCheckpoint) -> None:
        """Persist a checkpoint."""

    def load_latest(self, run_id: str) -> SessionCheckpoint | None:
        """Load the latest checkpoint for a run."""
