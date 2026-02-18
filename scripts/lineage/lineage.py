#!/usr/bin/env python3
from __future__ import annotations

from pipeline_common.lineage.api import MarquezApiClient
from _commands import LineageCommands
from _config import LineageQueryConfig
from _output import Printer, build_palette
from _parser import build_parser
from constants import LINEAGE_QUERY_ENV


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = LineageQueryConfig(
        api_base_url=str(LINEAGE_QUERY_ENV["marquez_api_url"]),
        job_namespace=str(LINEAGE_QUERY_ENV["lineage_job_namespace"]),
        dataset_namespace=str(LINEAGE_QUERY_ENV["lineage_dataset_namespace"]),
        no_color=bool(LINEAGE_QUERY_ENV["no_color"]),
    )

    api = MarquezApiClient(cfg.api_base_url)
    printer = Printer(build_palette(cfg.no_color))
    commands = LineageCommands(api=api, printer=printer, cfg=cfg)

    return commands.execute_command(args.command, args)


if __name__ == "__main__":
    raise SystemExit(main())
