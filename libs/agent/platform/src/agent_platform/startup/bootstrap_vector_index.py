"""Bootstrap a deterministic local vector fixture from the current repo snapshot."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Iterable

from ai_infra.retrieval.deterministic_hash_embedder import (
    DeterministicHashEmbedder,
)

MAX_FILE_BYTES = 24_000


def bootstrap_vector_index(
    workspace_root: str,
    output_path: str,
    ignore_file_path: str,
    embedder: DeterministicHashEmbedder,
) -> None:
    """Index the current repo snapshot using a gitignore-style exclude file."""

    repo = Path(workspace_root)
    repo_file_lister = RepositoryFileLister(
        workspace_root=repo,
        extra_ignore_file=ignore_file_path,
    )
    documents = []
    for path in repo_file_lister.iter_files():
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        relative_path = path.relative_to(repo).as_posix()
        content = path.read_text(errors="ignore")[:4000]
        documents.append(
            {
                "doc_id": relative_path.replace("/", "__"),
                "path": relative_path,
                "content": content,
                "vector": embedder.embed(content),
            }
        )
    Path(output_path).write_text(json.dumps({"documents": documents}, indent=2))


class RepositoryFileLister:
    """List repository files with optional Git and custom ignore behavior."""

    def __init__(
        self,
        workspace_root: Path,
        extra_ignore_file: str | None = None,
        include_gitignore: bool = True,
    ) -> None:
        self._root = workspace_root
        self._extra_ignore_file = extra_ignore_file
        self._include_gitignore = include_gitignore

        if not (self._root / ".git").exists():
            raise ValueError(f"{self._root} is not a git repository")

    def list_files(self) -> list[Path]:
        """Return repository files respecting configured ignore rules."""
        cmd = [
            "git",
            "-C",
            str(self._root),
            "ls-files",
            "--cached",
            "--others",
        ]

        if self._include_gitignore:
            cmd.append("--exclude-standard")

        if self._extra_ignore_file:
            ignore_path = Path(self._extra_ignore_file).resolve()
            cmd.append(f"--exclude-from={ignore_path}")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(exc.stderr.strip()) from exc

        return [self._root / path for path in sorted(result.stdout.splitlines())]

    def iter_files(self) -> Iterable[Path]:
        return iter(self.list_files())
