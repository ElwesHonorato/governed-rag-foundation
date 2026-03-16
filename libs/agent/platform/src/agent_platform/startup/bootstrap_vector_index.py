"""Bootstrap a deterministic local vector fixture from the current repo snapshot."""

from __future__ import annotations

import json
from pathlib import Path

from ai_infra.retrieval.deterministic_retrieval_embedder import (
    DeterministicRetrievalEmbedder,
)

ALLOWED_SUFFIXES = {".md", ".py", ".toml"}
IGNORED_PARTS = {".git", ".venv", "localdata", "__pycache__"}
MAX_FILE_BYTES = 24_000


def bootstrap_vector_index(
    workspace_root: str,
    output_path: str,
    embedder: DeterministicRetrievalEmbedder,
) -> None:
    """Index an allowlisted subset of the current repo snapshot."""

    repo = Path(workspace_root)
    documents = []
    for path in sorted(repo.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        if path.suffix not in ALLOWED_SUFFIXES:
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        relative_path = path.relative_to(repo).as_posix()
        if not relative_path.startswith(("docs/", "domains/", "libs/", "plan_tasks.md", "task.md")):
            continue
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
