from flask import Flask, jsonify, render_template, request

from vector_ui.config import Settings
from vector_ui.weaviate_client import WeaviateClient

ALLOWED_SORT_FIELDS = {"chunk_id", "doc_id", "source_key", "security_clearance"}


def create_app() -> Flask:
    settings = Settings.from_env()
    weaviate_client = WeaviateClient(
        weaviate_url=settings.weaviate_url,
        timeout_seconds=settings.query_timeout_seconds,
    )

    app = Flask(__name__)

    @app.get("/")
    def root() -> str:
        return render_template("ui.html")

    @app.get("/health")
    def health() -> tuple[dict[str, str], int]:
        return {"status": "ok", "service": "vector-ui"}, 200

    @app.post("/query")
    def query() -> tuple[dict[str, object], int]:
        payload = request.get_json(silent=True) or {}
        phrase = str(payload.get("phrase", "")).strip()
        doc_id = str(payload.get("doc_id", "")).strip()
        raw_limit = payload.get("limit", 25)
        sort_by = str(payload.get("sort_by", "")).strip()
        sort_order = str(payload.get("sort_order", "asc")).strip().lower()
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return jsonify({"error": "limit must be an integer"}), 400
        if sort_by and sort_by not in ALLOWED_SORT_FIELDS:
            return jsonify({"error": f"sort_by must be one of: {', '.join(sorted(ALLOWED_SORT_FIELDS))}"}), 400
        if sort_order not in {"asc", "desc"}:
            return jsonify({"error": "sort_order must be 'asc' or 'desc'"}), 400

        try:
            records, graphql_query = weaviate_client.search_chunks(
                phrase=phrase,
                doc_id=doc_id,
                limit=limit,
            )
        except Exception as exc:
            return jsonify({"error": f"weaviate query failed: {exc}"}), 502

        if sort_by:
            reverse = sort_order == "desc"
            records = sorted(records, key=lambda item: str(item.get(sort_by, "")), reverse=reverse)

        return jsonify({"count": len(records), "records": records, "graphql_query": graphql_query}), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
