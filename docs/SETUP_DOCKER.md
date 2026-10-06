# ResQGrid AI — Docker Setup Guide

This guide covers Docker and Docker Compose configuration.

---

## Overview

The project uses Docker Compose to orchestrate all services:

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `postgres` | postgis/postgis:16-3.4 | 5432 | Database with spatial extensions |
| `redis` | redis:7-alpine | 6379 | Cache and queue |
| `api` | Custom (Python 3.11) | 8000 | FastAPI backend |
| `web` | Custom (Node 20) | 3000 | Next.js frontend |

## Prerequisites

- Docker Desktop v24+ (includes Docker Compose v2)
- At least 4GB RAM allocated to Docker
- At least 20GB disk space

## Quick Start

```bash
# 1. Copy environment
cp .env.example .env

# 2. Start everything
docker compose up -d

# 3. Wait for services to be healthy
docker compose ps

# 4. Run migrations
docker exec -it resqgrid-api alembic upgrade head

# 5. Seed demo data
docker exec -it resqgrid-api python -m app.seed

# 6. Open the app
open http://localhost:3000      # Frontend
open http://localhost:8000/docs # API docs
```

## Service-by-Service

### Start Only Infrastructure

```bash
docker compose up -d postgres redis
```

### Start Only API

```bash
docker compose up -d api
```

### Start Only Frontend

```bash
docker compose up -d web
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f web
```

### Stop All Services

```bash
docker compose down
```

### Stop and Remove Data

```bash
# WARNING: Deletes all database data
docker compose down -v
```

## Docker Files

### API Dockerfile (services/api/Dockerfile)

- Base: `python:3.11-slim`
- Installs: libpq-dev, GDAL (for PostGIS)
- Python dependencies from requirements.txt
- Health check on `/health`

### Web Dockerfile (apps/web/Dockerfile)

- Multi-stage build (deps → builder → runner)
- Base: `node:20-alpine`
- Standalone Next.js output for minimal image
- Non-root user for security

## Environment Variables in Docker

Docker Compose reads from `.env` in the project root. Key overrides:

```env
# Override ports
APP_PORT=8000
POSTGRES_PORT=5432

# Database connection (inside Docker network)
DATABASE_URL=postgresql+asyncpg://resqgrid:resqgrid_dev_password@postgres:5432/resqgrid_ai
```

## Building Images

```bash
# Build all
docker compose build

# Build specific service
docker compose build api
docker compose build web

# Rebuild without cache
docker compose build --no-cache
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Container exits immediately | Check logs: `docker compose logs api` |
| Port already in use | Change port in `.env` or stop conflicting service |
| Build fails | Run `docker compose build --no-cache` |
| Database connection refused | Wait for healthcheck: `docker compose ps` should show "healthy" |
| Out of disk space | Run `docker system prune -a` |
| Slow builds | Use Docker BuildKit: `DOCKER_BUILDKIT=1 docker compose build` |

## Production Docker

For production, use the standalone builds:

```bash
# Build production images
docker compose -f docker-compose.yml build

# Run with production settings
docker compose up -d --build
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full production deployment guide.
