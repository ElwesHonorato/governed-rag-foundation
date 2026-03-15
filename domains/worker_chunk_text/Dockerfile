FROM python:3.11-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_REQUESTS_TIMEOUT=180 \
    POETRY_INSTALLER_PARALLEL=false \
    PIP_DEFAULT_TIMEOUT=180 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY domains/worker_chunk_text /app/domains/worker_chunk_text
COPY libs/pipeline-common /app/libs/pipeline-common

WORKDIR /app/domains/worker_chunk_text

RUN poetry install --only main

CMD ["poetry", "run", "worker-chunk-text"]
