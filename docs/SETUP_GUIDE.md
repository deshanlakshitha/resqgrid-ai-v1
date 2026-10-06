# ResQGrid AI — Complete Setup Guide

This guide walks you through setting up the entire ResQGrid AI project from scratch.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone and Configure](#clone-and-configure)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [Database Setup](#database-setup)
7. [AI Configuration](#ai-configuration)
8. [Running the Application](#running-the-application)
9. [Verify Everything Works](#verify-everything-works)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Install these tools before starting:

| Tool | Version | Download |
|------|---------|----------|
| **Docker Desktop** | v24+ | https://www.docker.com/products/docker-desktop |
| **Docker Compose** | v2+ (included with Docker Desktop) | — |
| **Python** | 3.11+ | https://www.python.org/downloads/ |
| **Node.js** | 18+ (LTS recommended) | https://nodejs.org/ |
| **npm** | 9+ (included with Node.js) | — |
| **Git** | 2.40+ | https://git-scm.com/ |
| **PostgreSQL** (optional, for local dev) | 16+ | https://www.postgresql.org/download/ |
| **Redis** (optional, for local dev) | 7+ | https://redis.io/download |

### Verify Installations

```bash
docker --version          # Should show 24.x or higher
docker compose version    # Should show v2.x
python --version          # Should show 3.11+
node --version            # Should show 18+
npm --version             # Should show 9+
git --version             # Should show 2.40+
```

---

## Clone and Configure

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/resqgrid-ai.git
cd resqgrid-ai
```

### Step 2: Create Environment File

```bash
cp .env.example .env
```

### Step 3: Edit `.env`

Open `.env` and update at minimum:

```env
# Required: Change to random secure strings
JWT_SECRET=generate-a-random-64-char-string-here
APP_SECRET_KEY=generate-another-random-string-here

# Optional: For real AI triage (leave empty for mock AI)
DASHSCOPE_API_KEY=your-alibaba-cloud-api-key

# Optional: For evidence upload (leave empty for local storage)
OSS_ACCESS_KEY_ID=your-oss-key
OSS_ACCESS_KEY_SECRET=your-oss-secret
```

To generate a random secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Infrastructure Setup

### Option A: Docker (Recommended)

```bash
# Start PostgreSQL and Redis
docker compose up -d postgres redis

# Verify they are running
docker compose ps
# Both should show "healthy"

# Check PostgreSQL
docker exec -it resqgrid-postgres psql -U resqgrid -c "SELECT version();"

# Check Redis
docker exec -it resqgrid-redis redis-cli ping
# Should return "PONG"
```

### Option B: Local Installation (Advanced)

If you prefer running PostgreSQL and Redis locally:

```bash
# PostgreSQL (macOS via Homebrew)
brew install postgresql@16 postgis
brew services start postgresql@16
createdb resqgrid_ai
psql resqgrid_ai -c "CREATE USER resqgrid WITH PASSWORD 'resqgrid_dev_password';"
psql resqgrid_ai -c "GRANT ALL PRIVILEGES ON DATABASE resqgrid_ai TO resqgrid;"
psql resqgrid_ai -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Redis (macOS via Homebrew)
brew install redis
brew services start redis
```

---

## Backend Setup

See [SETUP_BACKEND.md](SETUP_BACKEND.md) for detailed backend guide.

### Quick Start

```bash
# Navigate to API service
cd services/api

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Seed demo data
python -m app.seed

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- http://localhost:8000 (API root)
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

---

## Frontend Setup

See [SETUP_FRONTEND.md](SETUP_FRONTEND.md) for detailed frontend guide.

### Quick Start

```bash
# Navigate to web app
cd apps/web

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:3000.

---

## Database Setup

See [SETUP_DATABASE.md](SETUP_DATABASE.md) for detailed database guide.

### Create Initial Migration

```bash
cd services/api

# Generate initial migration from models
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Verify tables
docker exec -it resqgrid-postgres psql -U resqgrid -d resqgrid_ai -c "\dt"
```

### Seed Demo Data

```bash
python -m app.seed
```

This creates:
- 5 demo users (admin, dispatcher, responder x2, citizen)
- 20 incidents of various types and severities
- 30 resources (ambulances, fire trucks, boats, helicopters, teams, shelters, hospitals)
- 8 hazards and blocked roads

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@resqgrid.local | admin123 |
| Dispatcher | dispatcher@resqgrid.local | dispatch123 |
| Responder | responder1@resqgrid.local | respond123 |
| Citizen | citizen@resqgrid.local | citizen123 |

---

## AI Configuration

See [SETUP_AI.md](SETUP_AI.md) for detailed AI integration guide.

### Without API Key (Mock Mode)

The system automatically uses a mock AI adapter when no `DASHSCOPE_API_KEY` is configured. Mock triage returns realistic sample data.

### With Alibaba Cloud Model Studio

1. Get an API key: https://www.alibabacloud.com/help/en/model-studio/get-api-key
2. Set in `.env`:
   ```env
   DASHSCOPE_API_KEY=sk-your-api-key-here
   MODEL_STUDIO_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   MODEL_STUDIO_MODEL=qwen-plus
   ```

---

## Running the Application

### Option A: All-in-One Docker

```bash
# From project root
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Option B: Hybrid (Docker infra + local dev)

```bash
# Terminal 1: Start infrastructure
docker compose up -d postgres redis

# Terminal 2: Start API
cd services/api
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Start frontend
cd apps/web
npm run dev
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

---

## Verify Everything Works

### 1. Health Check

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"resqgrid-ai","version":"0.1.0"}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@resqgrid.local","password":"admin123"}'
# Save the access_token from the response
```

### 3. List Incidents

```bash
curl http://localhost:8000/api/v1/incidents \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
# Should return 20 seeded incidents
```

### 4. Dashboard Summary

```bash
curl http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
# Should return KPI counts
```

### 5. Frontend

Open http://localhost:3000 — you should see the command dashboard with incidents in the left panel and a map in the center.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `docker compose` fails | Ensure Docker Desktop is running |
| PostgreSQL won't start | Check port 5432 is not in use: `lsof -i :5432` |
| Redis won't start | Check port 6379 is not in use: `lsof -i :6379` |
| API can't connect to DB | Ensure DATABASE_URL in `.env` matches your setup |
| `alembic` command not found | Activate virtual environment: `source .venv/bin/activate` |
| Frontend shows blank page | Run `npm install` in `apps/web/` first |
| CORS error in browser | Check CORS_ORIGINS in `.env` includes `http://localhost:3000` |
| AI triage returns mock data | Set DASHSCOPE_API_KEY in `.env` for real AI |
| npm install fails | Ensure Node.js 18+ is installed |
| pip install fails | Ensure Python 3.11+ and pip are available |
