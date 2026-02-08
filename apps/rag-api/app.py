import os

from flask import Flask, jsonify, render_template, request

from llm_client import OllamaClient

app = Flask(__name__)


def dependency_config() -> dict[str, str | None]:
    return {
        "weaviate": os.getenv("WEAVIATE_URL"),
        "redis": os.getenv("REDIS_URL"),
        "s3": os.getenv("S3_ENDPOINT"),
        "marquez": os.getenv("MARQUEZ_URL"),
        "llm": os.getenv("LLM_URL"),
        "llm_model": os.getenv("LLM_MODEL"),
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

    prompt_text = raw_prompt.strip()
    if not prompt_text:
        return jsonify({"error": "prompt is required"}), 400
    if len(prompt_text) > 2000:
        return jsonify({"error": "prompt is too long (max 2000 characters)"}), 400

    llm_url = os.getenv("LLM_URL")
    llm_model = os.getenv("LLM_MODEL")
    llm_timeout_raw = os.getenv("LLM_TIMEOUT_SECONDS", "30")

    if not llm_url:
        return jsonify({"error": "LLM_URL is not configured"}), 500
    if not llm_model:
        return jsonify({"error": "LLM_MODEL is not configured"}), 500

    try:
        llm_timeout = float(llm_timeout_raw)
    except ValueError:
        return jsonify({"error": "LLM_TIMEOUT_SECONDS must be numeric"}), 500
    llm_client = OllamaClient(llm_url=llm_url, timeout_seconds=llm_timeout)

    try:
        llm_response = llm_client.generate(prompt=prompt_text, model=llm_model)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify(
        {
            "prompt": prompt_text,
            "model": llm_model,
            "response": llm_response,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
