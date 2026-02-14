FROM python:3.11-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/pipeline-common/src

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY domains/worker_index_weaviate/pyproject.toml /app/pyproject.toml
RUN poetry install --only main --no-root

COPY domains/worker_index_weaviate/src /app/src
COPY libs/pipeline-common/src /pipeline-common/src

CMD ["poetry", "run", "python", "-m", "app"]
