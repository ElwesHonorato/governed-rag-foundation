"""Agent-platform CLI."""

from __future__ import annotations

import argparse
import json

from agent_platform.application.execution_runtime_factory import ExecutionRuntimeFactory
from agent_platform.rag.rag_runtime_factory import RagRuntimeFactory
from agent_platform.startup.bootstrap import RuntimeBootstrapper
from agent_platform.startup.engine_factory import EngineFactory
from agent_platform.startup.retrieval_composition import RetrievalCompositionFactory
from agent_platform.startup.startup_assets_factory import StartupAssetsFactory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("objective")
    run_parser.add_argument("--skill", default="analyze_repository")

    subparsers.add_parser("capability-list")
    subparsers.add_parser("skill-list")

    session_show = subparsers.add_parser("session-show")
    session_show.add_argument("session_id")

    eval_run = subparsers.add_parser("eval-run")
    eval_run.add_argument("run_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    factory = EngineFactory(
        startup_assets_factory=StartupAssetsFactory(
            bootstrapper=RuntimeBootstrapper(),
            retrieval_composition_factory=RetrievalCompositionFactory(),
        ),
        execution_runtime_factory=ExecutionRuntimeFactory(),
        rag_runtime_factory=RagRuntimeFactory(),
    )
    app = factory.build()

    if args.command == "capability-list":
        print(json.dumps([item.to_dict() for item in app.list_capabilities()], indent=2))
        return 0
    if args.command == "skill-list":
        print(json.dumps(app.list_skills(), indent=2))
        return 0
    if args.command == "session-show":
        session = app.load_session(args.session_id)
        print(json.dumps(session.to_dict(), indent=2))
        return 0
    if args.command == "eval-run":
        evaluation = app.evaluate_run(args.run_id)
        print(json.dumps(evaluation.to_dict(), indent=2))
        return 0
    if args.command == "run":
        result = app.run_objective(objective=args.objective, skill_name=args.skill)
        print(json.dumps(result.to_dict(), indent=2))
        return 0
    raise ValueError(f"Unsupported command: {args.command}")
