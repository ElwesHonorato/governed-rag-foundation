from __future__ import annotations

import argparse
from enum import Enum


class LineageCommand(str, Enum):
    NAMESPACES = "namespaces"
    JOBS = "jobs"
    DATASETS = "datasets"
    SEARCH = "search"
    CHUNK = "chunk"


COMMAND_ARGS: dict[LineageCommand, tuple[str, str | None]] = {
    LineageCommand.NAMESPACES: ("List Marquez namespaces.", None),
    LineageCommand.JOBS: ("List jobs for a namespace.", "namespace"),
    LineageCommand.DATASETS: ("List datasets for a namespace.", "namespace"),
    LineageCommand.SEARCH: ("Search Marquez metadata.", "text"),
    LineageCommand.CHUNK: ("Search lineage for a specific chunk id.", "chunk_id"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 scripts/lineage/lineage.py")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command, (help_text, positional_arg) in COMMAND_ARGS.items():
        sub = subparsers.add_parser(command.value, help=help_text)
        if positional_arg is None:
            continue
        if command in (LineageCommand.JOBS, LineageCommand.DATASETS):
            sub.add_argument(positional_arg, nargs="?")
        else:
            sub.add_argument(positional_arg)

    return parser
