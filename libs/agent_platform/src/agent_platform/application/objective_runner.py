"""Application service for running an objective."""

from __future__ import annotations

from dataclasses import dataclass

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.kernel.agent_session_manager import AgentSessionManager
from ai_infra.services.capability_planning_service import CapabilityPlanningService
from ai_infra.services.run_supervisor import RunSupervisor
from agent_platform.application.skill_registry import SkillRegistry


@dataclass(frozen=True)
class ObjectiveRunner:
    """Coordinate the end-to-end objective execution flow."""

    session_manager: AgentSessionManager
    planning_service: CapabilityPlanningService
    supervisor: RunSupervisor
    skill_registry: SkillRegistry

    def run(self, *, objective: str, skill_name: str) -> AgentRun:
        session = self.session_manager.create_session(
            objective=objective, skill_name=skill_name
        )
        skill_definition = self.skill_registry.get(skill_name)
        plan = self.planning_service.build_plan(
            skill_name, objective, skill_definition.planning_config
        )
        run = self.supervisor.create_run(
            session_id=session.session_id,
            skill_name=skill_name,
            objective=objective,
            prompt_version="v1",
            execution_plan=plan,
        )
        session = self.session_manager.attach_run(session, run.run_id)
        completed_run = self.supervisor.run(run)
        self.session_manager.update_run_status(
            session, completed_run.run_id, completed_run.status
        )
        return completed_run
