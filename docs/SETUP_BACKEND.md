# ResQGrid AI — Backend Setup Guide

This guide covers the Python FastAPI backend service in detail.

---

## Architecture

The backend is a Python FastAPI application with:

- **Async SQLAlchemy** for database operations
- **Pydantic v2** for request/response validation
- **Alembic** for database migrations
- **JWT** for authentication
- **RBAC** (Role-Based Access Control) with 4 roles: citizen, responder, dispatcher, admin
- **AI Adapter Interface** for swappable LLM providers
- **Structured logging** via structlog

## Directory Structure

```
services/api/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── seed.py                 # Demo data seeder
│   ├── api/v1/                 # API route handlers
│   │   ├── router.py           # Route aggregator
│   │   └── routes/
│   │       ├── auth.py         # Authentication endpoints
│   │       ├── incidents.py    # Incident CRUD + triage/priority
│   │       ├── resources.py    # Resource management
│   │       ├── recommendations.py  # Approve/reject workflow
│   │       ├── assignments.py  # Assignment lifecycle
│   │       ├── dashboard.py    # KPI summary
│   │       ├── hazards.py      # Hazard management
│   │       ├── audit.py        # Audit log queries
│   │       ├── assistant.py    # AI command assistant
│   │       └── evidence.py     # File upload
│   ├── core/
│   │   ├── config.py           # Settings from env vars
│   │   ├── database.py         # Async DB engine
│   │   ├── security.py         # JWT + password hashing
│   │   └── deps.py             # Auth dependencies
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── base.py             # Base model with audit fields
│   │   ├── user.py             # User with RBAC roles
│   │   ├── incident.py         # Incident entity
│   │   ├── resource.py         # Resource entity
│   │   └── entities.py         # Recommendation, Assignment, Evidence, Hazard, AuditLog
│   ├── schemas/
│   │   └── schemas.py          # Pydantic request/response schemas
│   ├── services/               # Business logic
│   │   ├── triage_service.py   # AI triage orchestration
│   │   ├── priority_service.py # Deterministic priority engine
│   │   ├── recommendation_service.py  # Resource matching
│   │   ├── assistant_service.py # AI command assistant
│   │   └── storage_service.py  # Object storage (OSS/local)
│   ├── adapters/
│   │   └── ai_adapter.py       # AI provider interface (Model Studio + Mock)
│   └── middleware/
│       └── request_id.py       # Request ID tracking
├── alembic/                    # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/                      # Test suite
├── Dockerfile
├── requirements.txt
├── alembic.ini
└── pyproject.toml
```

## Step-by-Step Setup

### 1. Create Virtual Environment

```bash
cd services/api

# Create
python -m venv .venv

# Activate
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate          # Windows PowerShell

# Verify
python --version                # Should be 3.11+
which python                    # Should point to .venv
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

Copy from the root `.env.example` or create a service-specific `.env`:

```bash
# The app reads from the root .env or environment variables
# Make sure DATABASE_URL points to your PostgreSQL
echo $DATABASE_URL
```

### 4. Run Migrations

```bash
# Generate first migration (if needed)
alembic revision --autogenerate -m "Initial schema"

# Apply all migrations
alembic upgrade head

# Check current revision
alembic current
```

### 5. Seed Demo Data

```bash
python -m app.seed
```

### 6. Start Development Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Run Tests

```bash
python -m pytest tests/ -v --tb=short
```

### 8. Lint and Type Check

```bash
# Lint
python -m ruff check .

# Format
python -m ruff format .

# Type check
python -m mypy .
```

## API Endpoints Summary

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/auth/register | No | Register new user |
| POST | /api/v1/auth/login | No | Get JWT tokens |
| POST | /api/v1/auth/refresh | No | Refresh access token |
| GET | /api/v1/auth/me | Yes | Current user profile |
| POST | /api/v1/incidents | Yes | Create incident |
| GET | /api/v1/incidents | Yes | List incidents |
| GET | /api/v1/incidents/{id} | Yes | Get incident |
| PATCH | /api/v1/incidents/{id} | Dispatcher+ | Update incident |
| POST | /api/v1/incidents/{id}/triage | Dispatcher+ | Run AI triage |
| POST | /api/v1/incidents/{id}/priority | Dispatcher+ | Calculate priority |
| POST | /api/v1/incidents/{id}/recommendations | Dispatcher+ | Get recommendations |
| POST | /api/v1/resources | Dispatcher+ | Register resource |
| GET | /api/v1/resources | Yes | List resources |
| GET | /api/v1/resources/available | Yes | Available resources |
| POST | /api/v1/recommendations/{id}/approve | Dispatcher+ | Approve |
| POST | /api/v1/recommendations/{id}/reject | Dispatcher+ | Reject |
| POST | /api/v1/assignments | Dispatcher+ | Create assignment |
| PATCH | /api/v1/assignments/{id} | Yes | Update status |
| GET | /api/v1/dashboard/summary | Yes | KPI summary |
| POST | /api/v1/hazards | Yes | Report hazard |
| GET | /api/v1/hazards | Yes | List hazards |
| GET | /api/v1/audit/logs | Dispatcher+ | Query audit logs |
| POST | /api/v1/assistant/query | Dispatcher+ | Ask AI assistant |
| POST | /api/v1/evidence | Yes | Upload file |

## Creating New Migrations

```bash
# After modifying models:
alembic revision --autogenerate -m "Description of change"

# Review the generated migration file in alembic/versions/
# Then apply:
alembic upgrade head

# Rollback one step:
alembic downgrade -1
```
