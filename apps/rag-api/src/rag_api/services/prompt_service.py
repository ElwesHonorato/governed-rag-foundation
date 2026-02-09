
from rag_api.llm_client import OllamaClient


class PromptService:
    def __init__(self, *, llm_client: OllamaClient, model: str) -> None:
        self.llm_client = llm_client
        self.model = model

    def normalize_messages(self, payload: dict[str, object]) -> list[dict[str, str]]:
        raw_messages = payload.get("messages")
        if raw_messages is None:
            # Backward-compatible path for older clients still posting `prompt`.
            raw_prompt = payload.get("prompt", "")
            if not isinstance(raw_prompt, str):
                raise ValueError("prompt must be a string")
            prompt_text = raw_prompt.strip()
            if not prompt_text:
                raise ValueError("prompt is required")
            if len(prompt_text) > 2000:
                raise ValueError("prompt is too long (max 2000 characters)")
            return [{"role": "user", "content": prompt_text}]

        if not isinstance(raw_messages, list) or not raw_messages:
            raise ValueError("messages must be a non-empty list")

        messages: list[dict[str, str]] = []
        for item in raw_messages:
            if not isinstance(item, dict):
                raise ValueError("each message must be an object")
            role = item.get("role")
            content = item.get("content")
            if not isinstance(role, str) or not role.strip():
                raise ValueError("message role must be a non-empty string")
            if not isinstance(content, str):
                raise ValueError("message content must be a string")

            text = content.strip()
            if not text:
                raise ValueError("message content must not be empty")
            if len(text) > 4000:
                raise ValueError("message content is too long (max 4000 characters)")
            messages.append({"role": role.strip(), "content": text})

        return messages

    def run_prompt(self, *, messages: list[dict[str, str]]) -> dict[str, object]:
        response = self.llm_client.chat(messages=messages, model=self.model)
        assistant_message = {"role": "assistant", "content": response}
        return {
            "model": self.model,
            "response": response,
            "assistant_message": assistant_message,
        }

    def handle_prompt(self, payload: dict[str, object]) -> tuple[dict[str, object], int]:
        try:
            messages = self.normalize_messages(payload)
        except ValueError as exc:
            return {"error": str(exc)}, 400

        try:
            result = self.run_prompt(messages=messages)
        except RuntimeError as exc:
            return {"error": str(exc)}, 502

        return result, 200
