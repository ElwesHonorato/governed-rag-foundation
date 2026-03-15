"""Local deterministic synthesis adapter."""

from __future__ import annotations


class LocalModelGateway:
    """Deterministic stand-in for a synthesis model."""

    def synthesize(self, prompt: str, context: dict[str, object]) -> str:
        step_lines = []
        for item in context.get("step_results", []):
            capability_name = item["capability_name"]
            if capability_name == "vector_search":
                hits = item["output"].get("hits", [])
                hit_lines = ", ".join(hit["path"] for hit in hits[:3])
                step_lines.append(f"Vector hits: {hit_lines or 'none'}")
            elif capability_name == "filesystem_read":
                path = item["output"].get("path", "")
                preview = str(item["output"].get("content", ""))[:120].replace("\n", " ")
                step_lines.append(f"Read {path}: {preview}")
            elif capability_name == "command_run_safe":
                stdout = str(item["output"].get("stdout", "")).strip()
                step_lines.append(f"Command output: {stdout[:160]}")
        summary = "\n".join(f"- {line}" for line in step_lines if line)
        return (
            f"Objective: {context['objective']}\n"
            f"Skill: {context['skill_name']}\n"
            f"Findings:\n{summary or '- No tool findings were collected.'}"
        )
