# ResQGrid AI — Deployment Guide

---

## Deployment Options

| Option | Best For | Complexity |
|--------|----------|------------|
| Docker Compose (Local) | Development, demos | Low |
| Supabase + Upstash + Render (Free Cloud) | Hackathon / prototype | Low |
| Alibaba Cloud Container | Production | Medium |
| Function Compute + API Gateway | Serverless | Medium |
| Kubernetes | Large-scale production | High |

## Free Cloud Deployment (Supabase + Upstash + Render)

This is the fastest way to publish a fully working hosted prototype for judges.

### 1. Create the PostgreSQL database on Supabase

1. Go to [https://supabase.com](https://supabase.com) and sign up/log in.
2. Click **New project**.
3. Choose a name (e.g. `resqgrid-ai`), set the password, and pick a region close to your users (Singapore is good for Sri Lanka).
4. Wait for the project to be created.
5. In the left sidebar, go to **Project Settings → Database**.
6. Copy the **Connection string** under **URI**. It looks like:
   ```
   postgresql://postgres:[password]@db.xxxxx.supabase.co:5432/postgres
   ```
7. Go to the **SQL Editor** and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

### 2. Create Redis on Upstash

1. Go to [https://upstash.com](https://upstash.com) and sign up/log in.
2. Click **Create Database**.
3. Name it `resqgrid-redis` and pick a region close to Supabase.
4. Copy the **Redis URL** (starts with `redis://` or `rediss://`).

### 3. Deploy the backend on Render

1. Push your code to GitHub if you have not already.
2. Go to [https://render.com](https://render.com) and sign up/log in.
3. Click **New → Blueprint**.
4. Connect your GitHub repo (`deshanlakshitha/resqgrid-ai`).
5. Render will read the `render.yaml` file and create the service.
6. After the service is created, go to the service **Environment** tab and fill in:
   - `DATABASE_URL` = the Supabase connection string
   - `REDIS_URL` = the Upstash Redis URL
   - `JWT_SECRET` = a long random string (generate at [https://jwtsecret.com](https://jwtsecret.com) or use `openssl rand -hex 32`)
7. The first deploy will run `alembic upgrade head` automatically and start the API.
8. After the first deploy succeeds, open **Shell** in the Render dashboard and run:
   ```bash
   python -m app.seed
   ```
   This creates the demo users, incidents, resources, and hazards.

### 4. Update Vercel environment variable

1. Go to [https://vercel.com/dashboard](https://vercel.com/dashboard).
2. Open your ResQGrid AI project.
3. Go to **Settings → Environment Variables**.
4. Add or update:
   - `NEXT_PUBLIC_API_URL` = `https://resqgrid-api.onrender.com/api/v1`
     (replace `resqgrid-api.onrender.com` with your actual Render service URL)
5. Click **Save**, then go to **Deployments** and click **Redeploy** on the latest deployment.

### 5. Test the hosted prototype

- Open your Vercel URL.
- Log in with:
  - **Dispatcher**: `dispatcher@resqgrid.local` / `dispatch123`
  - **Citizen**: `citizen@resqgrid.local` / `citizen123`
- You should see the Colombo demo data on the map.

### Optional: Enable real AI

- Add `GEMINI_API_KEY` (Google AI Studio) or `DASHSCOPE_API_KEY` (Alibaba Cloud Model Studio) in Render environment variables.
- Without a key, the AI assistant still answers from live data using rule-based database queries.

## Docker Compose (Local/Dev)

```bash
cp .env.example .env
# Edit .env with real values

docker compose up -d --build
docker exec -it resqgrid-api alembic upgrade head
docker exec -it resqgrid-api python -m app.seed
```

## Alibaba Cloud Deployment

### Option 1: Container Platform

1. **Build and push images:**
   ```bash
   docker build -t registry.ap-southeast-1.aliyuncs.com/resqgrid/api -f services/api/Dockerfile .
   docker build -t registry.ap-southeast-1.aliyuncs.com/resqgrid/web -f apps/web/Dockerfile .
   docker push registry.ap-southeast-1.aliyuncs.com/resqgrid/api
   docker push registry.ap-southeast-1.aliyuncs.com/resqgrid/web
   ```

2. **Create RDS PostgreSQL instance** with PostGIS enabled
3. **Create Redis instance** via Alibaba Cloud
4. **Create OSS bucket** for evidence storage
5. **Deploy containers** to ACK (Kubernetes) or Container Service
6. **Configure API Gateway** for routing
7. **Set environment variables** in the container service

### Option 2: Function Compute

1. Package the FastAPI app as a Function Compute function
2. Configure API Gateway trigger
3. Connect to RDS PostgreSQL (see VPC configuration)
4. Set up OSS trigger for evidence processing

### Infrastructure Checklist

- [ ] RDS PostgreSQL with PostGIS
- [ ] Redis instance
- [ ] OSS bucket
- [ ] Model Studio API key
- [ ] SSL certificates
- [ ] Domain name (optional)
- [ ] Monitoring and alerting
- [ ] Log aggregation
- [ ] Backup schedule

## Production Environment Variables

```env
APP_ENV=production
APP_DEBUG=false
DATABASE_URL=postgresql+asyncpg://user:pass@rds-host:5432/resqgrid_ai
REDIS_URL=redis://redis-host:6379/0
JWT_SECRET=<strong-random-secret>
DASHSCOPE_API_KEY=<real-api-key>
OSS_ACCESS_KEY_ID=<oss-key>
OSS_ACCESS_KEY_SECRET=<oss-secret>
OSS_BUCKET=resqgrid-evidence-prod
CORS_ORIGINS=https://your-domain.com
LOG_LEVEL=WARNING
```

## CI/CD Pipeline

Example GitHub Actions workflow structure:

```yaml
# .github/workflows/deploy.yml
name: Deploy ResQGrid AI
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose up -d postgres redis
      - run: cd services/api && pip install -r requirements.txt && pytest
      - run: cd apps/web && npm ci && npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: docker compose build
      - run: # Push to registry and deploy
```

## Monitoring

Recommended monitoring:
- API response times and error rates
- Database connection pool usage
- Redis memory usage
- AI adapter response times
- Disk space for evidence uploads
- Audit log growth rate

## References

- Function Compute: https://www.alibabacloud.com/help/en/functioncompute/
- API Gateway: https://www.alibabacloud.com/help/en/api-gateway/
- RDS PostgreSQL: https://www.alibabacloud.com/help/en/rds/
