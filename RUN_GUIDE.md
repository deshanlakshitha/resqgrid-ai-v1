# How to Run ResQGrid AI (Your Machine)

Everything is already installed. Each day you only need **3 terminals**.

---

## One-Time Setup (Already Done — skip this)

If you ever need to redo it from scratch:

```powershell
# 1. Copy environment file
cd "D:\Cursor Projects\ResQGrid AI"
Copy-Item .env.example .env

# 2. Install backend dependencies (venv already exists at services\api\.venv)
cd services\api
py -3.11 -m venv .venv
.venv\Scripts\pip install -r requirements.txt

# 3. Install frontend dependencies
cd ..\..\apps\web
npm install
```

---

## Daily Run — Step by Step

### Terminal 1: Start the Database (PostgreSQL + Redis)

First make sure **Docker Desktop is running** (green whale icon in system tray).
If it's not, open it from the Start menu and wait ~30 seconds until it turns green.

```powershell
cd "D:\Cursor Projects\ResQGrid AI"
docker compose up -d postgres redis
```

Check they are healthy:

```powershell
docker compose ps
```

You should see `resqgrid-postgres` and `resqgrid-redis` both say `(healthy)`.

> This only needs to be done once per day (or after a PC restart).
> The database keeps your data — you do NOT need to re-run migrations or seed again.

---

### Terminal 2: Start the Backend API (FastAPI)

```powershell
cd "D:\Cursor Projects\ResQGrid AI\services\api"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Wait until you see:

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Keep this terminal open. To stop the backend later, press `Ctrl+C`.

---

### Terminal 3: Start the Frontend (Next.js)

```powershell
cd "D:\Cursor Projects\ResQGrid AI\apps\web"
npm run dev
```

Wait until you see:

```
▲ Next.js 14.2.35
- Local: http://localhost:3000
✓ Ready in 3s
```

Keep this terminal open. To stop the frontend later, press `Ctrl+C`.

---

### Open the App

| What | URL |
|------|-----|
| **Frontend (Command Center UI)** | http://localhost:3000 |
| **Backend API docs (Swagger)** | http://localhost:8000/docs |
| **Backend health check** | http://localhost:8000/health |

**Login credentials:**

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@resqgrid.local | admin123 |
| Dispatcher | dispatcher@resqgrid.local | dispatch123 |
| Responder | responder1@resqgrid.local | respond123 |
| Citizen | citizen@resqgrid.local | citizen123 |

---

## Try the Full Workflow (in Swagger UI)

Open http://localhost:8000/docs and follow this order:

1. **POST /api/v1/auth/login** — login as dispatcher → copy the `access_token`
2. Click the **Authorize** button (top right) → paste the token
3. **GET /api/v1/incidents** — see the 20 seeded incidents
4. **POST /api/v1/incidents/{id}/triage** — run AI triage (copy an incident ID from step 3)
5. **POST /api/v1/incidents/{id}/priority** — get the priority score
6. **POST /api/v1/incidents/{id}/recommendations** — get resource matches
7. **POST /api/v1/recommendations/{rec_id}/approve** — body: `{"approved": true}` → human approves
8. **GET /api/v1/audit/logs** — see the full audit trail of everything above

---

## Shutting Down

Reverse order:

1. In Terminal 3 (frontend): `Ctrl+C`
2. In Terminal 2 (backend): `Ctrl+C`
3. Stop the databases (optional — data is safe either way):

```powershell
cd "D:\Cursor Projects\ResQGrid AI"
docker compose stop
```

> `docker compose stop` keeps your data. NEVER use `docker compose down -v`
> (the `-v` flag deletes all database data permanently).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `docker: command not found` | Docker Desktop isn't running — open it and wait for green icon |
| `error while connecting... dockerDesktopLinuxEngine` | Same as above — engine still starting, wait 30s |
| Port 8000 already in use | An old backend is still running: `Get-Process python \| Stop-Process` then retry |
| Port 3000 already in use | An old frontend is still running: `Get-Process node \| Stop-Process` then retry (careful: closes other node apps too) |
| Login returns 401 | Check you're using the exact emails/passwords from the table above |
| `alembic upgrade head` errors | Database containers not healthy yet — re-check `docker compose ps` |
| Lost all data / empty incidents list | Re-seed: `cd services\api` then `.venv\Scripts\python.exe -m app.seed` |

### Reset the database completely (dangerous — wipes all data)

```powershell
cd "D:\Cursor Projects\ResQGrid AI"
docker compose down -v          # DELETES all data
docker compose up -d postgres redis
# wait until healthy, then:
cd services\api
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe -m app.seed
```

---

## Quick Reference — What Runs Where

```
Your PC
├── Docker Desktop
│   ├── resqgrid-postgres  → localhost:5432  (database, has all data)
│   └── resqgrid-redis     → localhost:6379  (cache)
├── Terminal 2: uvicorn     → localhost:8000  (FastAPI backend)
└── Terminal 3: next dev    → localhost:3000  (frontend)
```
