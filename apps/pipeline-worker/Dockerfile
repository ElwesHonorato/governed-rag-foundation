FROM python:3.11-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml /app/pyproject.toml
RUN poetry install --only main --no-root

COPY src /app/src
COPY worker.py /app/worker.py

CMD ["python", "-m", "pipeline_worker.app"]
