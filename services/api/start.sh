#!/bin/bash
# ResQGrid AI — Render deployment start script
# Runs Alembic migrations, then starts the FastAPI server.
set -e

echo "ResQGrid AI API starting up..."

# Diagnostic: confirm required env vars are present (do not print secrets)
echo "DATABASE_URL set: ${DATABASE_URL:+yes}"
echo "REDIS_URL set: ${REDIS_URL:+yes}"
echo "JWT_SECRET set: ${JWT_SECRET:+yes}"
echo "PORT: ${PORT:-8000}"

if [ -n "$DATABASE_URL" ]; then
    db_host=$(echo "$DATABASE_URL" | sed -n 's|.*@\([^:/]*\).*|\1|p')
    echo "DATABASE_URL host: $db_host"
fi

if [ -n "$REDIS_URL" ]; then
    redis_host=$(echo "$REDIS_URL" | sed -n 's|.*@\([^:/]*\).*|\1|p')
    echo "REDIS_URL host: $redis_host"
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting Uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
