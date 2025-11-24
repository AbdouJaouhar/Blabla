FROM ghcr.io/astral-sh/uv:alpine AS base

WORKDIR /app

COPY pyproject.toml .
COPY alembic.ini .
COPY alembic ./alembic
COPY libs ./libs
COPY services/api ./services/api
COPY scripts ./scripts

RUN uv sync --frozen

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "scripts/migrate.sh && uv run uvicorn services.api.server:app --host 0.0.0.0 --port 3000"]
