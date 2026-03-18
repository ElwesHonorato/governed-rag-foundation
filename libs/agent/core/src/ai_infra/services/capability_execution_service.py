"""Capability execution service."""

from __future__ import annotations

from ai_infra.contracts.agent_run import AgentRun
from ai_infra.contracts.capability_request import CapabilityRequest
from ai_infra.contracts.capability_result import CapabilityResult
from ai_infra.protocols.gateways.command_execution_gateway import (
    CommandExecutionGateway,
)
from ai_infra.protocols.gateways.filesystem_gateway import FilesystemGateway
from ai_infra.protocols.gateways.llm_gateway import LLMGateway
from ai_infra.protocols.gateways.vector_search_gateway import VectorSearchGateway
from ai_infra.services.prompt_assembly_service import PromptAssemblyService


class CapabilityExecutionService:
    """Dispatches requests to concrete capability backends."""

    def __init__(
        self,
        filesystem_gateway: FilesystemGateway,
        command_gateway: CommandExecutionGateway,
        vector_gateway: VectorSearchGateway,
        llm_gateway: LLMGateway,
        prompt_assembly_service: PromptAssemblyService,
    ) -> None:
        self._filesystem_gateway = filesystem_gateway
        self._command_gateway = command_gateway
        self._vector_gateway = vector_gateway
        self._llm_gateway = llm_gateway
        self._prompt_assembly_service = prompt_assembly_service

    def execute(self, request: CapabilityRequest, run: AgentRun) -> CapabilityResult:
        try:
            if request.capability_name == "filesystem_read":
                content = self._filesystem_gateway.read_text(str(request.input_payload["path"]))
                output = {"path": request.input_payload["path"], "content": content}
            elif request.capability_name == "command_run_safe":
                output = self._command_gateway.run(list(request.input_payload["command"]))
                if int(output.get("returncode", 0)) != 0:
                    raise ValueError(
                        f"Command exited with code {output['returncode']}: {output.get('stderr', '').strip()}"
                    )
            elif request.capability_name == "vector_search":
                query = str(request.input_payload["query"])
                top_k = int(request.input_payload.get("top_k", 3))
                output = {"hits": self._vector_gateway.search(query=query, top_k=top_k)}
            elif request.capability_name == "llm_synthesize":
                prompt_key = str(request.input_payload["prompt_key"])
                prompt, _context = self._prompt_assembly_service.assemble(
                    prompt_key=prompt_key,
                    run=run,
                )
                text = self._llm_gateway.generate(
                    prompt=prompt,
                    model=self._llm_gateway.resolve_model(),
                )
                output = {"text": text, "prompt_key": prompt_key}
            else:
                raise ValueError(f"Unsupported capability: {request.capability_name}")
        except Exception as exc:  # noqa: BLE001
            return CapabilityResult(
                capability_name=request.capability_name,
                step_id=request.step_id,
                success=False,
                error_message=str(exc),
            )
        return CapabilityResult(
            capability_name=request.capability_name,
            step_id=request.step_id,
            success=True,
            output=output,
        )
