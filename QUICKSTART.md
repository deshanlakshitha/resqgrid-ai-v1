# ResQGrid AI — Quick Start

Cross-platform (Windows PowerShell, macOS/Linux shell). From the project root:

## Step 1: Start Docker Services

```bash
docker compose up -d postgres redis
docker compose ps        # wait until both are "healthy"
```

## Step 2: Start the API Backend

Option A — Docker (recommended):

```bash
docker compose up -d api
```

Option B — Locally with Python 3.11:

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 3: Start the Frontend

```bash
cd apps/web
npm install
npm run dev
```

## Step 4: Open the App

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## AI Configuration (optional)

Triage works offline out of the box via the built-in local engine (ensemble mode
`offline_local_only`). To add an LLM ensemble partner, set either `GEMINI_API_KEY`
or `DASHSCOPE_API_KEY` in `services/api/.env`.

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@resqgrid.local | admin123 |
| Dispatcher | dispatcher@resqgrid.local | dispatch123 |
| Responder | responder1@resqgrid.local | respond123 |
| Citizen | citizen@resqgrid.local | citizen123 |

## Demo Highlight: AI Optimization

Log in as dispatcher/admin, create a few incidents, then:

```bash
curl -X POST http://localhost:8000/api/v1/assignments/optimize \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{}'
```

Returns the globally optimal incident→resource plan (Hungarian algorithm) with
kilometers saved vs the greedy baseline.
