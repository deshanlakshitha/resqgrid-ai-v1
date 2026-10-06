# ResQGrid AI — Deployment Guide

---

## Deployment Options

| Option | Best For | Complexity |
|--------|----------|------------|
| Docker Compose (Local) | Development, demos | Low |
| Alibaba Cloud Container | Production | Medium |
| Function Compute + API Gateway | Serverless | Medium |
| Kubernetes | Large-scale production | High |

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
