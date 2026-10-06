#!/bin/bash
# ResQGrid AI — Render deployment start script
# Runs Alembic migrations, then starts the FastAPI server.
set -e

echo "ResQGrid AI API starting up..."
echo "Running database migrations..."
alembic upgrade head

echo "Starting Uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
