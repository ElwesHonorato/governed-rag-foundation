FROM python:3.11-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_REQUESTS_TIMEOUT=180 \
    POETRY_INSTALLER_PARALLEL=false \
    PIP_DEFAULT_TIMEOUT=180 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/src:/pipeline-common/src

WORKDIR /app

RUN python3 -m pip install --no-cache-dir poetry

COPY domains/worker_metrics/pyproject.toml /app/pyproject.toml
RUN poetry install --only main --no-root

COPY domains/worker_metrics/src /app/src
COPY libs/pipeline-common/src /pipeline-common/src
COPY registry /app/registry

CMD ["poetry", "run", "python3", "-m", "app"]
