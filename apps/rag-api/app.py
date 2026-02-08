import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def root():
    return jsonify(
        {
            "service": "rag-api",
            "status": "ok",
            "dependencies": {
                "weaviate": os.getenv("WEAVIATE_URL"),
                "redis": os.getenv("REDIS_URL"),
                "s3": os.getenv("S3_ENDPOINT"),
                "marquez": os.getenv("MARQUEZ_URL"),
            },
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
