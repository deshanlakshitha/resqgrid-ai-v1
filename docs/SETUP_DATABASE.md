# ResQGrid AI — Database Setup Guide

This guide covers PostgreSQL + PostGIS database setup and management.

---

## Overview

ResQGrid AI uses PostgreSQL 16 with PostGIS 3.4 for spatial data. The database layer includes:

- **SQLAlchemy 2.0** async ORM
- **Alembic** for migrations
- **PostGIS** for geographic data
- **UUID** primary keys
- **Soft deletion** pattern
- **Audit timestamps** on all records
- **JSONB** columns for flexible AI output storage

## Tables

| Table | Description |
|-------|-------------|
| `users` | User accounts with RBAC roles |
| `incidents` | Emergency incident reports |
| `resources` | Response resources (vehicles, teams, shelters) |
| `recommendations` | AI-generated resource recommendations |
| `assignments` | Resource-to-incident assignments |
| `evidence` | Uploaded evidence (images, files) |
| `hazards` | Hazards and blocked roads |
| `audit_logs` | Immutable audit trail |

## Docker Setup (Recommended)

### Start PostgreSQL

```bash
docker compose up -d postgres
```

This starts PostgreSQL 16 with PostGIS 3.4 using the `postgis/postgis:16-3.4` image.

### Connect to Database

```bash
# Via Docker
docker exec -it resqgrid-postgres psql -U resqgrid -d resqgrid_ai

# Via connection string
psql "postgresql://resqgrid:resqgrid_dev_password@localhost:5432/resqgrid_ai"
```

### Verify Extensions

```sql
SELECT * FROM pg_extension;
-- Should show: postgis, plpgsql, uuid-ossp
```

## Local PostgreSQL Setup

### macOS

```bash
brew install postgresql@16
brew install postgis
brew services start postgresql@16

createdb resqgrid_ai
psql resqgrid_ai -c "CREATE USER resqgrid WITH PASSWORD 'resqgrid_dev_password';"
psql resqgrid_ai -c "GRANT ALL PRIVILEGES ON DATABASE resqgrid_ai TO resqgrid;"
psql resqgrid_ai -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql resqgrid_ai -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
```

### Linux (Ubuntu/Debian)

```bash
sudo apt install postgresql-16 postgresql-16-postgis-3
sudo -u postgres createdb resqgrid_ai
sudo -u postgres psql -c "CREATE USER resqgrid WITH PASSWORD 'resqgrid_dev_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE resqgrid_ai TO resqgrid;"
sudo -u postgres psql resqgrid_ai -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Windows

Download from https://www.postgresql.org/download/windows/ and install PostGIS via Stack Builder.

## Migrations

### Create a New Migration

```bash
cd services/api
source .venv/bin/activate

# Auto-generate from model changes
alembic revision --autogenerate -m "Add column X to table Y"

# Review the file in alembic/versions/
```

### Apply Migrations

```bash
alembic upgrade head        # Apply all pending
alembic upgrade +1          # Apply one migration
alembic downgrade -1        # Rollback one migration
alembic downgrade base      # Rollback everything
```

### Check Status

```bash
alembic current             # Current revision
alembic history             # Migration history
alembic heads               # Latest available revision
```

## Seeding

```bash
cd services/api
python -m app.seed
```

This creates the complete demo dataset. To reset:

```bash
# WARNING: Destroys all data
alembic downgrade base
alembic upgrade head
python -m app.seed
```

## Indexes

Key indexes to create for performance:

```sql
-- Incidents
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_created_at ON incidents(created_at DESC);
CREATE INDEX idx_incidents_location ON incidents USING GIST(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));

-- Resources
CREATE INDEX idx_resources_status ON resources(status);
CREATE INDEX idx_resources_type ON resources(resource_type);
CREATE INDEX idx_resources_location ON resources USING GIST(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326));

-- Audit logs
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at DESC);
```

## Backup

```bash
# Create backup
docker exec -it resqgrid-postgres pg_dump -U resqgrid resqgrid_ai > backup.sql

# Restore
cat backup.sql | docker exec -i resqgrid-postgres psql -U resqgrid -d resqgrid_ai
```
