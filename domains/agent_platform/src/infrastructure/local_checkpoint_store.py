"""File-backed checkpoint store."""

from __future__ import annotations

import json
from pathlib import Path

from ai_infra.contracts.session_checkpoint import SessionCheckpoint


class LocalCheckpointStore:
    """Persists checkpoints as JSON files."""

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, checkpoint: SessionCheckpoint) -> None:
        (self._base_dir / f"{checkpoint.run_id}.json").write_text(json.dumps(checkpoint.to_dict(), indent=2))

    def load_latest(self, run_id: str) -> SessionCheckpoint | None:
        path = self._base_dir / f"{run_id}.json"
        if not path.exists():
            return None
        payload = json.loads(path.read_text())
        return SessionCheckpoint(
            checkpoint_id=payload["checkpoint_id"],
            run_id=payload["run_id"],
            session_id=payload["session_id"],
            snapshot=payload["snapshot"],
            created_at=payload["created_at"],
        )
