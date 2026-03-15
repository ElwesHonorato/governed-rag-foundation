FROM python:3.11-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_REQUESTS_TIMEOUT=180 \
    POETRY_INSTALLER_PARALLEL=false \
    PIP_DEFAULT_TIMEOUT=180 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock
COPY src /app/src
RUN poetry install --only main

EXPOSE 8000

CMD ["poetry", "run", "vector-ui"]
