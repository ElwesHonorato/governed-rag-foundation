"""Prompt assembly service."""

from __future__ import annotations

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.gateways.prompt_template_repository import PromptTemplateRepository


class PromptAssemblyService:
    """Builds synthesis prompts from prior tool results."""

    def __init__(self, prompt_repository: PromptTemplateRepository) -> None:
        self._prompt_repository = prompt_repository

    def assemble(self, prompt_key: str, run: AgentRun) -> tuple[str, dict[str, object]]:
        prompt = self._prompt_repository.get_prompt(prompt_key)
        context = {
            "objective": run.objective,
            "skill_name": run.skill_name,
            "step_results": [result.to_dict() for result in run.step_results],
        }
        user_prompt = prompt.user_template.format(
            objective=run.objective,
            skill_name=run.skill_name,
            step_results="\n".join(
                f"- {result.capability_name}: {result.output or result.error_message}"
                for result in run.step_results
            ),
        )
        final_prompt = f"{prompt.system_instructions}\n\n{user_prompt}"
        return final_prompt, context
