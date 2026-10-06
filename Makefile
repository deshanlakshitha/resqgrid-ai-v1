# =============================================================================
# ResQGrid AI — Makefile
# =============================================================================
# Quick reference:
#   make help          — Show all available commands
#   make setup         — First-time project setup
#   make dev           — Start all dev services
#   make test          — Run all tests
# =============================================================================

.PHONY: help setup dev dev-api dev-web stop test lint format db-migrate db-seed db-reset clean

# Default target
help: ## Show this help message
	@echo "ResQGrid AI — Available Commands"
	@echo "================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---- Setup ----
setup: ## First-time project setup
	@echo "==> Copying environment file..."
	@if [ ! -f .env ]; then cp .env.example .env; echo ".env created from .env.example"; else echo ".env already exists"; fi
	@echo "==> Starting infrastructure (PostgreSQL + Redis)..."
	docker compose up -d postgres redis
	@echo "==> Waiting for services to be healthy..."
	@sleep 5
	@echo "==> Running database migrations..."
	$(MAKE) db-migrate
	@echo "==> Seeding demo data..."
	$(MAKE) db-seed
	@echo "==> Installing frontend dependencies..."
	cd apps/web && npm install
	@echo "==> Setup complete! Run 'make dev' to start all services."

# ---- Development ----
dev: ## Start all services (API + Web + infra)
	docker compose up -d postgres redis
	docker compose up api web

dev-infra: ## Start only infrastructure (PostgreSQL + Redis)
	docker compose up -d postgres redis

dev-api: ## Start only the backend API (requires infra running)
	cd services/api && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-web: ## Start only the frontend (requires API running)
	cd apps/web && npm run dev

stop: ## Stop all Docker services
	docker compose down

stop-volumes: ## Stop all services and remove volumes (DESTRUCTIVE)
	docker compose down -v

# ---- Database ----
db-migrate: ## Run database migrations
	cd services/api && alembic upgrade head

db-seed: ## Seed demo data into the database
	cd services/api && python -m app.seed

db-reset: ## Drop and recreate database, then migrate and seed (DESTRUCTIVE)
	cd services/api && alembic downgrade base
	cd services/api && alembic upgrade head
	cd services/api && python -m app.seed

db-shell: ## Open PostgreSQL interactive shell
	docker exec -it resqgrid-postgres psql -U resqgrid -d resqgrid_ai

# ---- Testing ----
test: ## Run all tests (backend + frontend)
	$(MAKE) test-api
	$(MAKE) test-web

test-api: ## Run backend tests
	cd services/api && python -m pytest tests/ -v --tb=short

test-web: ## Run frontend tests
	cd apps/web && npm test --passWithNoTests

# ---- Quality ----
lint: ## Run all linters
	$(MAKE) lint-api
	$(MAKE) lint-web

lint-api: ## Lint backend code
	cd services/api && python -m ruff check . && python -m mypy .

lint-web: ## Lint frontend code
	cd apps/web && npm run lint

format: ## Format all code
	cd services/api && python -m ruff format .
	cd apps/web && npm run format

# ---- Build ----
build: ## Build all Docker images
	docker compose build

build-api: ## Build API Docker image
	docker compose build api

build-web: ## Build Web Docker image
	docker compose build web

# ---- Utilities ----
clean: ## Remove all build artifacts and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Cleaned build artifacts."

logs: ## Tail logs from all running containers
	docker compose logs -f

shell-api: ## Open a shell inside the API container
	docker exec -it resqgrid-api bash
