from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from functools import wraps
from urllib import error

from pipeline_common.lineage.api import MarquezApiClient
from _config import LineageQueryConfig
from _output import Printer


class LineageCommands:
    def __init__(self, api: MarquezApiClient, printer: Printer, cfg: LineageQueryConfig) -> None:
        self.api = api
        self.printer = printer
        self.cfg = cfg

    def namespaces(self) -> int:
        self.printer.print_json(self.api.namespaces())
        return 0

    def jobs(self, namespace: str | None) -> int:
        self.printer.print_json(self.api.jobs(namespace or self.cfg.job_namespace))
        return 0

    def datasets(self, namespace: str | None) -> int:
        self.printer.print_json(self.api.datasets(namespace or self.cfg.dataset_namespace))
        return 0

    def search(self, query: str) -> int:
        self.printer.print_json(self.api.search(query))
        return 0

    def chunk(self, chunk_id: str) -> int:
        self.printer.header("Chunk Lookup")
        print(f"chunk_id: {chunk_id}")
        print(f"api_url: {self.cfg.api_base_url}")
        self.printer.header("Marquez Search")
        payload = self.api.search(chunk_id)
        total = int(payload.get("totalCount", 0))
        if total > 0:
            self.printer.ok(f"Marquez search found {total} result(s).")
        else:
            self.printer.warn("Marquez search returned 0 results.")
        self.printer.print_json(payload)
        self.printer.info("Tip: set NO_COLOR=1 to disable ANSI colors.")
        return 0

    def execute(self, command: str, args: argparse.Namespace) -> int:
        command_map: dict[str, Callable[[], int]] = {
            "namespaces": lambda: self.namespaces(),
            "jobs": lambda: self.jobs(getattr(args, "namespace", None)),
            "datasets": lambda: self.datasets(getattr(args, "namespace", None)),
            "search": lambda: self.search(getattr(args, "text")),
            "chunk": lambda: self.chunk(getattr(args, "chunk_id")),
        }
        runner = command_map.get(command)
        if runner is None:
            raise ValueError(f"Unknown command: {command}")
        return runner()

    def _with_command_error_handling(func: Callable[..., int]) -> Callable[..., int]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> int:
            try:
                return func(*args, **kwargs)
            except error.HTTPError as exc:
                print(f"HTTP error from Marquez: {exc.code}", file=sys.stderr)
                return 1
            except error.URLError as exc:
                print(f"Cannot reach Marquez API: {exc.reason}", file=sys.stderr)
                return 1
            except OSError as exc:
                print(f"I/O error: {exc}", file=sys.stderr)
                return 1

        return wrapper

    @_with_command_error_handling
    def execute_command(self, command: str, args: argparse.Namespace) -> int:
        return self.execute(command, args)
