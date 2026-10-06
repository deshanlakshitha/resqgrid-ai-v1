-- ResQGrid AI — Database Initialization Script
-- This runs automatically when the PostgreSQL container starts for the first time.

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for common queries
-- (Actual tables are created via Alembic migrations)
