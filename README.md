# ResQGrid AI — Intelligent Emergency Resource Network

> **AI recommends. Humans approve. Every important decision is explainable and auditable.**

ResQGrid AI is a production-quality MVP that helps emergency operators collect incidents, use AI to structure and triage reports, calculate explainable priority, match resources, and coordinate human-approved response actions.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Architecture Overview](#architecture-overview)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Setup Guides](#setup-guides)
- [API Reference](#api-reference)
- [AI Triage Contract](#ai-triage-contract)
- [Priority Engine](#priority-engine)
- [Resource Matching](#resource-matching)
- [Safety & Security](#safety--security)
- [Demo Scenario](#demo-scenario)
- [Build Phases](#build-phases)
- [Testing](#testing)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## Problem Statement

Emergency information is fragmented across citizens, responders, hospitals, shelters, resource providers, weather feeds, sensors, and other sources. During a rapidly evolving disaster, operators need to know:

- Which incidents are most urgent?
- Who is at risk?
- What resources are available?
- Which resource should be assigned?
- Which routes are currently feasible?
- What changed since the last decision?

ResQGrid AI turns these fragmented inputs into a live operational picture.

---

## Architecture Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                  │
│   Citizen (Mobile Web)   │   Dispatcher (Desktop)   │ Responder│
└──────────┬───────────────┴────────────┬──────────────┴────┬─────┘
           │                            │                   │
           ▼                            ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Next.js Frontend (TypeScript)                   │
│   Incident Form │ Command Dashboard │ Map │ Resource Panel      │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST + WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Python)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Auth/RBAC│ │Incidents │ │Resources │ │ Audit    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ AI Triage│ │ Priority │ │Resource  │ │ Hazards  │           │
│  │ (Qwen)   │ │ Engine   │ │ Matching │ │ & Routes │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└──────┬───────────────┬──────────────┬──────────────┬────────────┘
       │               │              │              │
       ▼               ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ PostgreSQL │ │   Redis    │ │  Alibaba   │ │  Alibaba   │
│ + PostGIS  │ │  (Cache/   │ │  Model     │ │  Cloud OSS │
│            │ │   Queue)   │ │  Studio    │ │  (Storage) │
└────────────┘ └────────────┘ └────────────┘ └────────────┘
```

### Core Data Flow

```text
Citizen / Sensor / Operator
          │
          ▼
    Incident Intake
          │
          ▼
   Normalize + Validate
          │
          ▼
      AI Triage
          │
          ▼
 Explainable Priority Score
          │
          ▼
 Resource Matching + Route Risk
          │
          ▼
 Human Approval
          │
          ▼
 Dispatch / Responder Update
          │
          ▼
 New Events → Re-plan
```

---

## Technology Stack

| Layer           | Technology                                   |
|----------------|----------------------------------------------|
| Frontend        | Next.js 14+ / TypeScript / Tailwind CSS       |
| Maps            | MapLibre GL JS / Leaflet                      |
| Backend         | Python 3.11+ / FastAPI                        |
| Database        | PostgreSQL 16 + PostGIS 3.4                   |
| Cache / Queue   | Redis 7                                       |
| AI / LLM        | Alibaba Cloud Model Studio / Qwen             |
| Object Storage  | Alibaba Cloud OSS (S3-compatible)             |
| ORM             | SQLAlchemy 2.0 + Alembic                      |
| Validation      | Pydantic v2                                   |
| Deployment      | Docker + Docker Compose                       |
| Cloud Deploy    | Alibaba Cloud Function Compute / API Gateway  |

---

## Repository Structure

```text
resqgrid-ai/
├── apps/
│   └── web/                          # Next.js frontend application
│       ├── src/
│       │   ├── app/                  # Next.js App Router pages
│       │   ├── components/           # Reusable UI components
│       │   ├── hooks/                # Custom React hooks
│       │   ├── lib/                  # Utility functions & API client
│       │   ├── stores/               # State management (Zustand)
│       │   ├── styles/               # Global styles
│       │   └── types/                # TypeScript type definitions
│       ├── public/                   # Static assets
│       ├── Dockerfile
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       └── package.json
│
├── services/
│   ├── api/                          # FastAPI backend application
│   │   ├── app/
│   │   │   ├── api/                  # Route handlers (v1)
│   │   │   ├── core/                 # Config, security, dependencies
│   │   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── schemas/              # Pydantic request/response schemas
│   │   │   ├── services/             # Business logic layer
│   │   │   ├── adapters/             # External service adapters
│   │   │   ├── middleware/            # Request middleware
│   │   │   └── utils/                # Helper utilities
│   │   ├── alembic/                  # Database migrations
│   │   ├── tests/                    # Backend test suite
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── alembic.ini
│   │   └── pyproject.toml
│   │
│   ├── ai/                           # AI triage & analysis service
│   │   ├── triage/                   # AI triage pipeline
│   │   ├── assistant/                # Command assistant
│   │   ├── vision/                   # Image evidence analysis
│   │   └── adapters/                 # Model provider adapters
│   │
│   ├── risk/                         # Hazard & route risk service
│   │   ├── hazards/                  # Hazard management
│   │   └── routes/                   # Route risk calculation
│   │
│   └── allocation/                   # Resource allocation service
│       ├── matcher/                  # Resource matching engine
│       └── optimizer/                # Allocation optimization
│
├── packages/
│   ├── types/                        # Shared TypeScript type definitions
│   └── config/                       # Shared configuration constants
│
├── db/
│   ├── init/                         # Database initialization scripts
│   ├── migrations/                   # Standalone migration files
│   └── seed/                         # Seed data for demo scenario
│
├── infra/                            # Infrastructure & deployment
│   ├── docker/                       # Additional Docker configs
│   ├── k8s/                          # Kubernetes manifests (future)
│   └── terraform/                    # Terraform configs (future)
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md               # Detailed architecture docs
│   ├── API_REFERENCE.md              # Full API reference
│   ├── SETUP_GUIDE.md                # Complete setup guide
│   ├── DEPLOYMENT.md                 # Deployment guide
│   ├── SECURITY.md                   # Security policies
│   └── MASTER_CODING_AGENT_PROMPT.md # Coding agent prompt
│
├── tests/                            # Integration & E2E tests
│   ├── integration/
│   └── e2e/
│
├── .env.example                      # Environment variable template
├── .gitignore                        # Git ignore rules
├── docker-compose.yml                # Docker Compose for all services
├── Makefile                          # Common development commands
└── README.md                         # This file
```

---

## Quick Start

### Prerequisites

- **Docker** & **Docker Compose** v2+
- **Python** 3.11+ (for local API development)
- **Node.js** 18+ and npm 9+ (for local frontend development)
- **Git**

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/resqgrid-ai.git
cd resqgrid-ai

# 2. Create your environment file
cp .env.example .env
# Edit .env with your API keys (DASHSCOPE_API_KEY at minimum)

# 3. Start everything with Docker Compose
docker compose up -d

# 4. Run database migrations and seed demo data
docker exec -it resqgrid-api alembic upgrade head
docker exec -it resqgrid-api python -m app.seed

# 5. Open the application
# Frontend:  http://localhost:3000
# API docs:  http://localhost:8000/docs
# API root:  http://localhost:8000/api/v1
```

For detailed step-by-step instructions, see [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md).

---

## Setup Guides

Detailed setup guides for each component:

| Guide | Description |
|-------|-------------|
| [Complete Setup Guide](docs/SETUP_GUIDE.md) | End-to-end setup from scratch |
| [Backend API Setup](docs/SETUP_BACKEND.md) | FastAPI backend development setup |
| [Frontend Setup](docs/SETUP_FRONTEND.md) | Next.js frontend development setup |
| [Database Setup](docs/SETUP_DATABASE.md) | PostgreSQL + PostGIS setup and migrations |
| [AI Integration](docs/SETUP_AI.md) | Alibaba Cloud Model Studio / Qwen setup |
| [Docker Setup](docs/SETUP_DOCKER.md) | Docker and Docker Compose guide |
| [Deployment Guide](docs/DEPLOYMENT.md) | Production deployment on Alibaba Cloud |

---

## API Reference

All endpoints are versioned under `/api/v1`. Interactive documentation is available at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc` (ReDoc).

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login` | Login and get JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET  | `/api/v1/auth/me` | Get current user profile |

### Incidents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/v1/incidents` | Create a new incident report |
| GET    | `/api/v1/incidents` | List all incidents (filterable) |
| GET    | `/api/v1/incidents/{id}` | Get incident details |
| PATCH  | `/api/v1/incidents/{id}` | Update incident |
| POST   | `/api/v1/incidents/{id}/triage` | Run AI triage on incident |
| POST   | `/api/v1/incidents/{id}/priority` | Calculate priority score |
| POST   | `/api/v1/incidents/{id}/recommendations` | Generate resource recommendations |

### Resources

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/v1/resources` | Register a resource |
| GET    | `/api/v1/resources` | List all resources |
| GET    | `/api/v1/resources/available` | List available resources |
| GET    | `/api/v1/resources/{id}` | Get resource details |
| PATCH  | `/api/v1/resources/{id}` | Update resource |

### Recommendations & Approvals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/v1/recommendations` | List recommendations |
| POST   | `/api/v1/recommendations/{id}/approve` | Approve a recommendation |
| POST   | `/api/v1/recommendations/{id}/reject` | Reject a recommendation |

### Assignments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/v1/assignments` | Create assignment |
| PATCH  | `/api/v1/assignments/{id}` | Update assignment status |
| GET    | `/api/v1/assignments` | List assignments |

### Evidence

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/v1/evidence` | Upload evidence (image/file) |
| GET    | `/api/v1/evidence/{id}` | Get evidence details |

### Dashboard & Assistant

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/v1/dashboard/summary` | Get dashboard KPI summary |
| POST   | `/api/v1/assistant/query` | Query AI command assistant |

### Hazards

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/v1/hazards` | Report a hazard |
| GET    | `/api/v1/hazards` | List active hazards |
| PATCH  | `/api/v1/hazards/{id}` | Update hazard status |

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/v1/audit/logs` | Query audit logs |
| GET    | `/api/v1/audit/logs/{id}` | Get specific audit entry |

Full API documentation: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

## AI Triage Contract

The AI triage system uses Alibaba Cloud Model Studio (Qwen) behind an adapter interface. All AI output is validated against this Pydantic schema before use:

```json
{
  "incident_type": "flood",
  "severity": "critical",
  "people_at_risk": 12,
  "vulnerable_people": 4,
  "medical_need": true,
  "immediate_needs": ["evacuation", "medical"],
  "evidence_quality": 0.86,
  "confidence": 0.91,
  "reason_codes": ["rapid_water_rise", "elderly_person", "medical_need"]
}
```

### AI Rules

- If information is missing, return `null`/`unknown` — never invent data.
- Return `confidence` separately from `severity`.
- Include short `reason_codes` that map to deterministic UI explanations.
- Treat citizen claims as reports, not verified facts.
- Never infer exact medical diagnoses.
- Never expose restricted personal data through the command assistant.

---

## Priority Engine

The priority engine calculates a deterministic, configurable, explainable score:

```text
Priority =
  0.30 × LifeRisk +
  0.20 × MedicalUrgency +
  0.15 × PeopleAtRisk +
  0.15 × EnvironmentalRisk +
  0.10 × TimeSensitivity +
  0.10 × EvidenceConfidence
```

All factors are normalized to 0–100. Weights are stored in configuration and are **not** claimed to be scientifically validated. Each score component is returned with reason codes for explainability.

---

## Resource Matching

Resources have: type, status, location, capacity, capabilities, organization, current assignment, and operating constraints.

A recommendation includes:
- Selected resource(s)
- Estimated ETA
- Compatibility reasons
- Constraints
- Confidence score
- Alternatives
- **Human approval required = true**

---

## Safety & Security

### Non-Negotiable Safety Rule

This is a **decision-support system**. AI may recommend; an authorized human **must** approve dispatch, evacuation, medical allocation, or other high-impact actions.

### Security Measures

- JWT-based authentication with RBAC (citizen, responder, dispatcher, admin)
- All AI output validated against Pydantic schemas
- Never trust LLM output as executable authorization
- Secrets never hard-coded (environment variables only)
- Audit logging for every recommendation and approval
- Prompt-injection defenses around tool use
- CORS configured for allowed origins
- Input sanitization on all endpoints
- Rate limiting on public endpoints

---

## Demo Scenario

The system is seeded with a fictional city/campus:

| Entity     | Count |
|------------|-------|
| Incidents  | 20    |
| Resources  | 30    |
| Shelters   | 5     |
| Hospitals  | 3     |
| Hazards    | 5     |
| Blocked Roads | 3  |

### Demo Flow

1. **Citizen** submits a flood emergency report
2. **AI** structures the report and assigns triage data
3. **Priority engine** calculates and updates the score
4. **System** recommends the best available resource
5. **Operator** approves the recommendation
6. **Responder** accepts the assignment
7. A road is marked **blocked**
8. **System** recalculates and proposes an alternative route/resource
9. **Command assistant** explains the current top 3 priorities

---

## Build Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Repository structure, architecture, environment, database | Foundation |
| 2 | Auth/RBAC, incidents, resources, audit logs | Core CRUD |
| 3 | Dashboard UI and interactive map | Frontend |
| 4 | Deterministic priority engine | Scoring |
| 5 | Model Studio/Qwen adapter and AI triage | AI Integration |
| 6 | Resource recommendations + human approval | Workflow |
| 7 | Hazards, route risk, and re-planning | Risk Layer |
| 8 | Evidence/image upload pipeline | Media |
| 9 | Notifications system | Alerts |
| 10 | Testing, security hardening, deployment, demo polish | Polish |

---

## Testing

```bash
# Run all tests
make test

# Backend tests only
make test-api

# Frontend tests only
make test-web

# With coverage
cd services/api && python -m pytest tests/ --cov=app --cov-report=html
```

---

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full production deployment instructions.

### Docker (Local)

```bash
docker compose --file docker-compose.yml up -d --build
```

### Alibaba Cloud

- **Function Compute** for serverless API hosting
- **API Gateway** for routing and access control
- **RDS PostgreSQL** for managed database
- **OSS** for evidence storage
- **Model Studio** for AI inference

---

## Environment Variables

See [.env.example](.env.example) for the complete list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `JWT_SECRET` | Yes | Secret key for JWT signing |
| `DASHSCOPE_API_KEY` | Yes | Alibaba Cloud Model Studio API key |
| `MODEL_STUDIO_BASE_URL` | No | Model Studio endpoint (has default) |
| `MODEL_STUDIO_MODEL` | No | Model name (default: qwen-plus) |
| `OSS_BUCKET` | No | OSS bucket for evidence storage |
| `CORS_ORIGINS` | No | Allowed CORS origins |

---

## Contributing

1. Create a feature branch from `main`
2. Make small, reviewable commits
3. Write tests for new functionality
4. Run `make lint` before submitting
5. Update documentation as the system evolves

---

## License

This project is built for the Alibaba Cloud Buildathon. See individual component licenses.

---

**Project Principle:** *Detect → Understand → Prioritize → Allocate → Approve → Respond → Re-plan → Learn*
