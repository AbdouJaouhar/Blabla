#!/usr/bin/env bash
set -e

if [ -n "$DATABASE_URL" ]; then
  sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = ${DATABASE_URL}|" alembic.ini
fi

uv run alembic upgrade head
