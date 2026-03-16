"""Process entrypoint for the agent-platform CLI."""

from __future__ import annotations

import argparse
import json

from agent_settings.settings import (
    EnvironmentSettingsProvider,
    SettingsBundle,
    SettingsRequest,
)
from agent_platform.agent_runtime.execution_runtime_factory import (
    ExecutionRuntimeFactory,
)
from agent_platform.grounded_response.grounded_response_factory import (
    GroundedResponseFactory,
)
from agent_platform.startup.bootstrap import RuntimeBootstrapper
from agent_platform.startup.command_gateway_factory import CommandGatewayFactory
from agent_platform.startup.engine_factory import (
    Engine,
    EngineFactory,
    EngineGatewayFactories,
    EngineRuntimeFactories,
    EngineStartupServices,
)
from agent_platform.startup.filesystem_gateway_factory import (
    FilesystemGatewayFactory,
)
from agent_platform.startup.local_state_stores_factory import LocalStateStoresFactory
from agent_platform.startup.llm_gateway_factory import LLMGatewayFactory
from agent_platform.startup.retrieval_gateway_factory import RetrievalGatewayFactory
from agent_platform.startup.retrieval_embedder_factory import (
    RetrievalEmbedderFactory,
)
from agent_platform.startup.vector_gateway_factory import VectorGatewayFactory


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
    argument_parser: argparse.ArgumentParser = _build_parser()
    parsed_args: argparse.Namespace = argument_parser.parse_args(argv)
    agent_settings: SettingsBundle = EnvironmentSettingsProvider(
        SettingsRequest(llm=True, retrieval=True)
    ).bundle
    engine_factory: EngineFactory = EngineFactory(
        startup_services=EngineStartupServices(
            bootstrapper=RuntimeBootstrapper(),
            retrieval_embedder_factory=RetrievalEmbedderFactory(),
            local_state_stores_factory=LocalStateStoresFactory(),
        ),
        gateway_factories=EngineGatewayFactories(
            filesystem=FilesystemGatewayFactory(),
            command=CommandGatewayFactory(),
            vector=VectorGatewayFactory(),
            llm=LLMGatewayFactory(),
            retrieval=RetrievalGatewayFactory(),
        ),
        runtime_factories=EngineRuntimeFactories(
            execution=ExecutionRuntimeFactory(),
            grounded_response=GroundedResponseFactory(),
        ),
        settings=agent_settings,
    )
    agent_cli_engine: Engine = engine_factory.build()

    if parsed_args.command == "capability-list":
        print(json.dumps([item.to_dict() for item in agent_cli_engine.list_capabilities()], indent=2))
        return 0
    if parsed_args.command == "skill-list":
        print(json.dumps(agent_cli_engine.list_skills(), indent=2))
        return 0
    if parsed_args.command == "session-show":
        session = agent_cli_engine.load_session(parsed_args.session_id)
        print(json.dumps(session.to_dict(), indent=2))
        return 0
    if parsed_args.command == "eval-run":
        evaluation = agent_cli_engine.evaluate_run(parsed_args.run_id)
        print(json.dumps(evaluation.to_dict(), indent=2))
        return 0
    if parsed_args.command == "run":
        result = agent_cli_engine.run_objective(
            objective=parsed_args.objective,
            skill_name=parsed_args.skill,
        )
        print(json.dumps(result.to_dict(), indent=2))
        return 0
    raise ValueError(f"Unsupported command: {parsed_args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
