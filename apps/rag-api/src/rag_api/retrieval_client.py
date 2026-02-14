import hashlib
import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    chunk_text: str
    source_key: str
    security_clearance: str
    distance: float | None


class RetrievalClient:
    def __init__(
        self,
        *,
        weaviate_url: str,
        embedding_dim: int,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.weaviate_url = weaviate_url.rstrip("/")
        self.embedding_dim = embedding_dim
        self.timeout_seconds = timeout_seconds

    def retrieve(self, *, query_text: str, limit: int) -> list[RetrievedChunk]:
        query = query_text.strip()
        if not query:
            return []
        safe_limit = max(1, min(limit, 20))

        try:
            like_results = self._like_search(query=query, limit=safe_limit)
            if like_results:
                return like_results
        except Exception:
            pass

        return self._near_vector_search(query=query, limit=safe_limit)

    def _near_vector_search(self, *, query: str, limit: int) -> list[RetrievedChunk]:
        vector = self._deterministic_embedding(query)
        vector_values = ",".join(f"{value:.8f}" for value in vector)
        gql = (
            "{Get{DocumentChunk("
            + f"nearVector:{{vector:[{vector_values}]}}"
            + f",limit:{limit})"
            + "{chunk_id doc_id chunk_text source_key security_clearance _additional{distance}}}}"
        )
        payload = self._graphql(gql)
        return self._parse_chunks(payload)

    def _like_search(self, *, query: str, limit: int) -> list[RetrievedChunk]:
        terms = _query_terms(query)
        if not terms:
            terms = [query.strip()]

        operands = []
        for term in terms[:6]:
            escaped = _escape_graphql_text(term)
            operands.append(f'{{path:["chunk_text"],operator:Like,valueText:"*{escaped}*"}}')

        if len(operands) == 1:
            where_clause = operands[0]
        else:
            where_clause = "{operator:Or,operands:[" + ",".join(operands) + "]}"

        gql = (
            "{Get{DocumentChunk("
            + f"where:{where_clause}"
            + f",limit:{limit})"
            + "{chunk_id doc_id chunk_text source_key security_clearance}}}"
        )
        payload = self._graphql(gql)
        return self._parse_chunks(payload)

    def _graphql(self, gql: str) -> dict[str, Any]:
        url = f"{self.weaviate_url}/v1/graphql"
        req = request.Request(
            url=url,
            method="POST",
            data=json.dumps({"query": gql}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Weaviate HTTP {exc.code}: {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Weaviate connection error: {exc.reason}") from exc
        data = json.loads(text) if text else {}
        if not isinstance(data, dict):
            raise RuntimeError("Invalid Weaviate response payload")
        if "errors" in data:
            raise RuntimeError(f"Weaviate GraphQL errors: {data['errors']}")
        return data

    def _parse_chunks(self, payload: dict[str, Any]) -> list[RetrievedChunk]:
        data = payload.get("data", {})
        get_payload = data.get("Get", {}) if isinstance(data, dict) else {}
        raw_items = get_payload.get("DocumentChunk", []) if isinstance(get_payload, dict) else []
        if not isinstance(raw_items, list):
            return []

        chunks: list[RetrievedChunk] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            additional = item.get("_additional")
            distance: float | None = None
            if isinstance(additional, dict):
                raw_distance = additional.get("distance")
                if isinstance(raw_distance, (float, int)):
                    distance = float(raw_distance)

            chunks.append(
                RetrievedChunk(
                    chunk_id=str(item.get("chunk_id", "")),
                    doc_id=str(item.get("doc_id", "")),
                    chunk_text=str(item.get("chunk_text", "")),
                    source_key=str(item.get("source_key", "")),
                    security_clearance=str(item.get("security_clearance", "")),
                    distance=distance,
                )
            )
        return chunks

    def _deterministic_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        for index in range(self.embedding_dim):
            byte = digest[index % len(digest)]
            values.append((byte / 255.0) * 2.0 - 1.0)
        return values


def _escape_graphql_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _query_terms(query: str) -> list[str]:
    parts = [piece.strip(".,:;!?()[]{}\"'").lower() for piece in query.split()]
    filtered = [part for part in parts if len(part) >= 4]
    unique: list[str] = []
    for term in filtered:
        if term not in unique:
            unique.append(term)
    return unique
