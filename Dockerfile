FROM python:3-slim

RUN pip install poetry

WORKDIR /app
COPY poetry.lock pyproject.toml .env /app/
COPY config_docker.toml /app/config.toml
COPY automate_crypto /app/automate_crypto/

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-dev