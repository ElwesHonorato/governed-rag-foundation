import json
from typing import Any
from urllib import request


class WeaviateClient:
    def __init__(self, *, weaviate_url: str, timeout_seconds: int) -> None:
        self.weaviate_url = weaviate_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def search_chunks(
        self,
        *,
        phrase: str,
        doc_id: str,
        limit: int,
    ) -> tuple[list[dict[str, Any]], str]:
        query = self._build_query(phrase=phrase, doc_id=doc_id, limit=limit)
        payload = self._http_json(
            f"{self.weaviate_url}/v1/graphql",
            method="POST",
            payload={"query": query},
        )
        data = payload.get("data", {})
        get_payload = data.get("Get", {}) if isinstance(data, dict) else {}
        chunks = get_payload.get("DocumentChunk", []) if isinstance(get_payload, dict) else []
        records = list(chunks) if isinstance(chunks, list) else []
        return records, query

    def _http_json(self, url: str, *, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
        req = request.Request(url=url, method=method, data=body, headers=headers)
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
        return json.loads(response_body) if response_body else {}

    def _build_query(self, *, phrase: str, doc_id: str, limit: int) -> str:
        where_clauses: list[str] = []
        phrase_value = phrase.strip()
        doc_id_value = doc_id.strip()

        if phrase_value:
            escaped_phrase = _escape_graphql_text(phrase_value)
            where_clauses.append(
                '{path:["chunk_text"],operator:Like,valueText:"*' + escaped_phrase + '*"}'
            )
        if doc_id_value:
            escaped_doc_id = _escape_graphql_text(doc_id_value)
            where_clauses.append(
                '{path:["doc_id"],operator:Equal,valueText:"' + escaped_doc_id + '"}'
            )

        where = ""
        if len(where_clauses) == 1:
            where = f"where:{where_clauses[0]},"
        elif len(where_clauses) > 1:
            where = "where:{operator:And,operands:[" + ",".join(where_clauses) + "]},"

        safe_limit = max(1, min(limit, 100))
        return (
            "{Get{DocumentChunk("
            + where
            + f"limit:{safe_limit})"
            + "{chunk_id doc_id chunk_text source_key security_clearance}}}"
        )


def _escape_graphql_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
