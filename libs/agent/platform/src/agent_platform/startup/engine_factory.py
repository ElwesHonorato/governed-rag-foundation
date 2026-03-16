"""Composition root for the local agent-platform runtime."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.agent_session import AgentSession
from ai_infra.contracts.capability_descriptor import CapabilityDescriptor
from ai_infra.contracts.evaluation_run import EvaluationRun
from ai_infra.evaluation.offline_evaluation_runner import OfflineEvaluationRunner
from ai_infra.registry.capability_registry import CapabilityRegistry
from agent_platform.application.objective_runner import ObjectiveRunner
from agent_platform.application.execution_runtime_factory import ExecutionRuntimeFactory
from agent_platform.application.skill_registry import SkillRegistry
from agent_platform.infrastructure.local_run_store import LocalRunStore
from agent_platform.infrastructure.local_session_store import LocalSessionStore
from agent_platform.rag.rag_runtime_factory import RagRuntimeFactory
from agent_platform.rag.service import RagService
from agent_platform.rag.contracts import RagResponse
from agent_platform.startup.startup_assets_factory import StartupAssetsFactory


@dataclass(frozen=True)
class Engine:
    """Narrow application-facing runtime boundary."""

    _capability_registry: CapabilityRegistry
    _skill_registry: SkillRegistry
    _session_store: LocalSessionStore
    _run_store: LocalRunStore
    _evaluation_runner: OfflineEvaluationRunner
    _objective_runner: ObjectiveRunner
    _rag_service: RagService

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return self._capability_registry.list_capabilities()

    def list_skills(self) -> list[str]:
        return self._skill_registry.names()

    def load_session(self, session_id: str) -> AgentSession:
        return self._session_store.load_session(session_id)

    def load_run(self, run_id: str) -> AgentRun:
        return self._run_store.load_run(run_id)

    def evaluate_run(self, run_id: str) -> EvaluationRun:
        return self._evaluation_runner.evaluate(self.load_run(run_id))

    def query_rag(self, body: dict[str, object]) -> RagResponse:
        return self._rag_service.respond(body)

    def run_objective(self, objective: str, skill_name: str) -> AgentRun:
        return self._objective_runner.run(objective=objective, skill_name=skill_name)


class EngineFactory:
    """Build the local runtime graph for agent-platform."""

    def __init__(
        self,
        *,
        startup_assets_factory: StartupAssetsFactory,
        execution_runtime_factory: ExecutionRuntimeFactory,
        rag_runtime_factory: RagRuntimeFactory,
    ) -> None:
        self._startup_assets_factory = startup_assets_factory
        self._execution_runtime_factory = execution_runtime_factory
        self._rag_runtime_factory = rag_runtime_factory

    def build(self) -> Engine:
        assets = self._startup_assets_factory.build()
        execution_runtime = self._execution_runtime_factory.build(assets)
        rag_service = self._rag_runtime_factory.build(assets)
        return Engine(
            _capability_registry=assets.capability_registry,
            _skill_registry=assets.skill_registry,
            _session_store=assets.stores.session_store,
            _run_store=assets.stores.run_store,
            _evaluation_runner=execution_runtime.evaluation_runner,
            _objective_runner=execution_runtime.objective_runner,
            _rag_service=rag_service,
        )
