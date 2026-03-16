"""Retrieval-grounded response orchestration."""

from __future__ import annotations

from agent_platform.llm.ollama_client import OllamaClient
from agent_platform.rag.contracts import Citation, RagResponse
from agent_platform.retrieval.weaviate_client import RetrievedChunk, WeaviateRetrievalClient


class RagService:
    """Runs retrieval-grounded chat against the configured vector store and LLM."""

    max_quote_chars = 400

    def __init__(
        self,
        *,
        llm_client: OllamaClient,
        retrieval_client: WeaviateRetrievalClient,
        model: str,
        retrieval_limit: int,
    ) -> None:
        self._llm_client = llm_client
        self._retrieval_client = retrieval_client
        self._model = model
        self._retrieval_limit = retrieval_limit

    def respond(self, payload: dict[str, object]) -> RagResponse:
        messages = self.normalize_messages(payload)
        return self.run(messages=messages)

    def normalize_messages(self, payload: dict[str, object]) -> list[dict[str, str]]:
        raw_messages = payload.get("messages")
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

    def run(self, *, messages: list[dict[str, str]]) -> RagResponse:
        user_query = self._latest_user_query(messages)
        retrieval_cap = max(1, min(self._retrieval_limit, 8))
        retrieved = self._retrieval_client.retrieve(query_text=user_query, limit=retrieval_cap)
        grounded_messages = self._build_grounded_messages(messages=messages, retrieved=retrieved)
        response = self._llm_client.chat(messages=grounded_messages, model=self._model)
        assistant_message = {"role": "assistant", "content": response}
        citations = [
            Citation(
                source_uri=chunk.source_uri,
                doc_id=chunk.doc_id,
                chunk_id=chunk.chunk_id,
                quote=self._quote_excerpt(chunk.chunk_text),
                distance=chunk.distance,
            )
            for chunk in retrieved
        ]
        return RagResponse(
            model=self._model,
            response=response,
            assistant_message=assistant_message,
            citations=citations,
        )

    def _latest_user_query(self, messages: list[dict[str, str]]) -> str:
        for message in reversed(messages):
            if message["role"] == "user":
                return message["content"]
        return messages[-1]["content"] if messages else ""

    def _build_grounded_messages(
        self,
        *,
        messages: list[dict[str, str]],
        retrieved: list[RetrievedChunk],
    ) -> list[dict[str, str]]:
        instruction = (
            "You are a retrieval-grounded assistant. Use only the provided CONTEXT.\n"
            "If context is insufficient, say so.\n"
            "For every factual claim, cite exact source_uri values in square brackets like "
            "[s3a://bucket/02_raw/example.html].\n"
            "When possible, include exact quoted snippets from context."
        )
        if retrieved:
            context_lines = []
            for chunk in retrieved:
                source_uri = chunk.source_uri or "unknown-source"
                quote = self._quote_excerpt(chunk.chunk_text)
                context_lines.append(f"source_uri={source_uri}\nquote=\"{quote}\"")
            context_block = "CONTEXT:\n" + "\n\n".join(context_lines)
        else:
            context_block = "CONTEXT:\n(no matching context retrieved from vector database)"
        system_message = {"role": "system", "content": f"{instruction}\n\n{context_block}"}
        return [system_message, *messages]

    def _quote_excerpt(self, text: str) -> str:
        content = (text or "").strip()
        if len(content) <= self.max_quote_chars:
            return content
        return content[: self.max_quote_chars] + "..."
