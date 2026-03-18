FROM python:3.11.14-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_REQUESTS_TIMEOUT=180 \
    POETRY_INSTALLER_PARALLEL=false \
    PIP_DEFAULT_TIMEOUT=180 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN python3 -m pip install --no-cache-dir poetry

COPY domains/agent_api /app/domains/agent_api
COPY libs/agent/platform /app/libs/agent/platform
COPY libs/agent/core /app/libs/agent/core
COPY libs/agent/settings /app/libs/agent/settings

WORKDIR /app/domains/agent_api

RUN poetry install --only main

EXPOSE 8010

CMD ["poetry", "run", "agent-api"]
