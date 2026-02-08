import os

from flask import Flask, jsonify, render_template, request

from prompt_engine import build_funny_reply

app = Flask(__name__)


def dependency_config() -> dict[str, str | None]:
    return {
        "weaviate": os.getenv("WEAVIATE_URL"),
        "redis": os.getenv("REDIS_URL"),
        "s3": os.getenv("S3_ENDPOINT"),
        "marquez": os.getenv("MARQUEZ_URL"),
    }


@app.get("/")
def root():
    return jsonify(
        {
            "service": "rag-api",
            "status": "ok",
            "dependencies": dependency_config(),
        }
    )


@app.get("/ui")
def ui():
    return render_template("ui.html")


@app.post("/prompt")
def prompt():
    payload = request.get_json(silent=True)
    raw_prompt = (payload or {}).get("prompt", "")

    if not isinstance(raw_prompt, str):
        return jsonify({"error": "prompt must be a string"}), 400

    try:
        reply = build_funny_reply(raw_prompt)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(reply)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
