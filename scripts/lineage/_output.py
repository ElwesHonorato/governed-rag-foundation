from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Palette:
    reset: str = ""
    bold: str = ""
    dim: str = ""
    blue: str = ""
    cyan: str = ""
    green: str = ""
    yellow: str = ""


def build_palette(no_color: bool) -> Palette:
    if no_color or not sys.stdout.isatty():
        return Palette()
    return Palette(
        reset="\033[0m",
        bold="\033[1m",
        dim="\033[2m",
        blue="\033[34m",
        cyan="\033[36m",
        green="\033[32m",
        yellow="\033[33m",
    )


class Printer:
    def __init__(self, palette: Palette) -> None:
        self.p = palette

    def header(self, title: str) -> None:
        print(f"\n{self.p.blue}{self.p.bold}==== {title} ===={self.p.reset}")
        print(f"{self.p.dim}{'-' * 60}{self.p.reset}")

    def ok(self, msg: str) -> None:
        print(f"{self.p.green}[OK]{self.p.reset} {msg}")

    def warn(self, msg: str) -> None:
        print(f"{self.p.yellow}[WARN]{self.p.reset} {msg}")

    def info(self, msg: str) -> None:
        print(f"{self.p.cyan}[INFO]{self.p.reset} {msg}")

    @staticmethod
    def print_json(payload: Any) -> None:
        print(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=False))
