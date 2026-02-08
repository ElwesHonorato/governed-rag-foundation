FROM python:3.11-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml /app/pyproject.toml
RUN poetry install --only main --no-root

COPY app.py prompt_engine.py /app/
COPY templates /app/templates
COPY static /app/static

EXPOSE 8000

CMD ["python", "app.py"]
