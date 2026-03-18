FROM python:3.11.14-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_REQUESTS_TIMEOUT=180 \
    POETRY_INSTALLER_PARALLEL=false \
    PIP_DEFAULT_TIMEOUT=180 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY domains/ai_ui /app/domains/ai_ui
COPY libs/agent/core /app/libs/agent/core
COPY libs/agent/settings /app/libs/agent/settings

WORKDIR /app/domains/ai_ui

RUN poetry install --only main

EXPOSE 8000

CMD ["poetry", "run", "ai-ui"]
