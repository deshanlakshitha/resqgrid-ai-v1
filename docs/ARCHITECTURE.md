# ResQGrid AI — Architecture Document

---

## System Architecture

ResQGrid AI is a decision-support system for emergency resource coordination. AI recommends; humans approve; every important decision is explainable and auditable.

### High-Level Architecture

```text
┌───────────────────────────────────────────────────────────────┐
│                         CLIENTS                                │
│  Citizen (Mobile Web)  │  Dispatcher (Desktop)  │  Responder  │
└────────┬───────────────┴──────────┬─────────────┴──────┬──────┘
         │                          │                     │
         ▼                          ▼                     ▼
┌───────────────────────────────────────────────────────────────┐
│              Next.js Frontend (TypeScript + Tailwind)          │
│  Incident Form │ Dashboard │ Map │ Detail Panel │ Assistant   │
└─────────────────────────────┬─────────────────────────────────┘
                              │ REST API + WebSocket
                              ▼
┌───────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                          │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐           │
│  │ Auth    │ │Incidents │ │Resources │ │ Audit   │           │
│  │ RBAC    │ │CRUD      │ │Registry  │ │ Logger  │           │
│  └─────────┘ └──────────┘ └──────────┘ └─────────┘           │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐           │
│  │AI Triage│ │ Priority │ │Resource  │ │ Hazards │           │
│  │Adapter  │ │ Engine   │ │Matching  │ │ & Routes│           │
│  └─────────┘ └──────────┘ └──────────┘ └─────────┘           │
└──────┬──────────────┬──────────────┬──────────────┬───────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│ PostgreSQL│ │  Redis    │ │ Alibaba   │ │ Alibaba   │
│ + PostGIS │ │ Cache/Q   │ │ Model     │ │ Cloud OSS │
│           │ │           │ │ Studio    │ │ (Storage) │
└───────────┘ └───────────┘ └───────────┘ └───────────┘
```

### Design Principles

1. **Human-in-the-loop** — AI never makes autonomous dispatch decisions
2. **Explainability** — Every score has components and reason codes
3. **Auditability** — Every action is logged immutably
4. **Swappability** — AI providers behind adapter interface
5. **Configurability** — Priority weights, thresholds, and rules are configurable
6. **Security** — RBAC, JWT auth, validated inputs, no secrets in code

### Data Flow

1. Citizen/sensor reports incident → API validates and stores
2. AI triage extracts structured data → validated against schema
3. Priority engine calculates deterministic score → explainable components
4. Resource matcher finds compatible available resources → ranked recommendations
5. Human operator reviews and approves/rejects → audit logged
6. Assignment created → responder notified → status tracked
7. New events (blocked road, new hazard) → re-plan triggered

### Priority Engine

Deterministic, configurable scoring:

```
Priority = 0.30 × LifeRisk + 0.20 × MedicalUrgency + 0.15 × PeopleAtRisk
         + 0.15 × EnvironmentalRisk + 0.10 × TimeSensitivity + 0.10 × EvidenceConfidence
```

All factors normalized to 0–100. Weights are configurable and NOT scientifically validated.

### Security Model

- JWT authentication (access + refresh tokens)
- RBAC: citizen, responder, dispatcher, admin
- Role-based endpoint protection
- All AI output validated by Pydantic schemas
- Request ID tracking for traceability
- CORS configured for allowed origins
- Audit logging of all significant operations
- Secrets via environment variables only
