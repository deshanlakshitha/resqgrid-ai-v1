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

### AI Pipeline

Two first-class AI components run inside the API service — no external AI call is required for either to work, so the system degrades gracefully offline.

#### 1. Hybrid Triage Ensemble (`app/ai/triage/`)

Incident text is triaged by **two engines whose outputs are merged**, not by a single LLM call:

- **Local engine** (`local_engine.py`) — a deterministic NLP pipeline that always runs, with zero dependencies and zero API keys. It scores per-incident-type lexicons (flood, fire, earthquake, landslide, accident, medical, hazmat, infrastructure), handles negation ("smoke but **no fire**"), extracts numeric counts via regex ("**3 people** trapped"), and applies severity escalators/de-escalators plus vulnerable-population detection (child, elderly, pregnant).
- **LLM adapter** — an optional second opinion behind the existing adapter interface (Alibaba Model Studio, OpenAI-compatible). If it errors or is unconfigured, triage proceeds on the local engine alone.

`ensemble.py` merges both into one `TriageOutput`-compatible result:

- **Agreement score** — weighted blend of severity agreement (0.5), incident-type agreement (0.3), and medical-need agreement (0.2).
- **Calibrated confidence** — engines that agree combine via noisy-or (agreeing engines are more likely right); calibrated against the agreement score.
- **Safety-first escalation** — a severity disagreement of ≥2 levels escalates to the higher severity, sets `disagreement_flag = true`, and dampens confidence so a human reviews it. People-count conflicts are flagged the same way.

The full ensemble block — both engines' raw outputs, agreement score, and disagreement flags — is persisted in `incident.triage_data`, giving the UI an explainable, per-engine audit trail. The `MockAIAdapter` is used in unit tests only and never at runtime.

#### 2. Global Assignment Optimizer (`app/allocation/optimizer.py`)

Resource-to-incident matching is a **global optimization**, not greedy first-fit:

- **Algorithm** — pure-Python Hungarian method (Kuhn–Munkres, O(n³)) over a rectangular cost matrix; no third-party solver.
- **Cost model** — haversine distance, inflated by the hazard route penalty used elsewhere in the system, plus a type-mismatch penalty. A resource whose `max_range_km` is exceeded gets an effectively infinite cost and is never assigned.
- **Baseline comparison** — the optimal plan is always compared against a greedy baseline; the response reports `savings_km` and `savings_pct`, so dispatchers see the measured value of optimal assignment.
- **Endpoint** — `POST /api/v1/assignments/optimize` (dispatcher/admin) returns an `AssignmentPlan`: ordered `assignments`, `unassigned_incident_ids`, `algorithm`, and the greedy comparison. Humans still approve every assignment — the optimizer proposes, dispatchers dispose.

Both components are deterministic (local engine, optimizer) or schema-validated (LLM output through Pydantic), keeping every AI decision explainable and auditable per the design principles above.

### Offline-First Field Reporting

Responders and citizens in disaster zones routinely lose connectivity, so incident submission is built to be retried safely:

- **Client outbox** — if a report cannot reach the server (network failure, not a server rejection), the web app stores it in an IndexedDB outbox together with a client-generated incident UUID, and tells the user it will sync automatically.
- **Idempotent replay** — on reconnect (browser `online` event or app load), queued reports are replayed in order with the *same* UUID. `POST /api/v1/incidents` accepts a client-supplied id: the database primary key dedupes concurrent/duplicate replays, a replay returns the original incident with HTTP 200 instead of creating a second row, and an id owned by a different user is rejected with 409.
- **Server-side guard** — because dedupe is enforced by the primary key (not client behavior), any client — mobile app, SMS gateway, integration — gets the same exactly-once guarantee.

### Security Model

- JWT authentication (access + refresh tokens)
- RBAC: citizen, responder, dispatcher, admin
- Role-based endpoint protection
- All AI output validated by Pydantic schemas
- Request ID tracking for traceability
- CORS configured for allowed origins
- Audit logging of all significant operations
- Secrets via environment variables only
