# ResQGrid AI — Quick Start (Windows)

After Docker Desktop is fully set up (green status in system tray):

## Step 1: Start Docker Services

Open PowerShell in the project root:

```powershell
cd "D:\Cursor Projects\ResQGrid AI"
docker compose up -d postgres redis
```

Wait for them to be healthy:

```powershell
docker compose ps
```

## Step 2: Start the API Backend

Option A — Docker (recommended):
```powershell
docker compose up -d api
```

Option B — Run locally with Python 3.11:
```powershell
cd services\api
.venv\Scripts\activate
alembic upgrade head
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 3: Start the Frontend

```powershell
cd apps\web
npm install
npm run dev
```

## Step 4: Open the App

- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@resqgrid.local | admin123 |
| Dispatcher | dispatcher@resqgrid.local | dispatch123 |
| Responder | responder1@resqgrid.local | respond123 |
| Citizen | citizen@resqgrid.local | citizen123 |
