SHELL := /bin/sh

COMPOSE ?= docker compose
PYTHON ?= python3
NPM ?= npm

BACKEND_DIR := backend
FRONTEND_DIR := frontend

BACKEND_ENV := $(BACKEND_DIR)/.env
FRONTEND_ENV_LOCAL := $(FRONTEND_DIR)/.env.local
MSG ?= new_migration

.PHONY: help env-init frontend-env-init docker-build docker-up docker-up-build docker-down docker-restart docker-ps docker-logs docker-logs-backend docker-logs-frontend docker-logs-db docker-shell-backend docker-shell-db docker-db-cli docker-migrate docker-migration backend-install backend-dev backend-migrate backend-test frontend-install frontend-dev frontend-lint lint test health docker-clean

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "}; /^[a-zA-Z0-9_.-]+:.*## / {printf "%-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

env-init: ## Create backend/.env from backend/.env.example if it does not exist
	@test -f $(BACKEND_ENV) || cp $(BACKEND_DIR)/.env.example $(BACKEND_ENV)
	@printf "backend env ready: %s\n" "$(BACKEND_ENV)"

frontend-env-init: ## Create frontend/.env.local for local frontend-to-backend proxy
	@test -f $(FRONTEND_ENV_LOCAL) || printf 'BACKEND_URL=http://localhost:8000\n' > $(FRONTEND_ENV_LOCAL)
	@printf "frontend env ready: %s\n" "$(FRONTEND_ENV_LOCAL)"

docker-build: ## Build Docker images
	$(COMPOSE) build

docker-up: ## Start Docker services in background
	$(COMPOSE) up -d

docker-up-build: ## Build and start Docker services in background
	$(COMPOSE) up -d --build

docker-down: ## Stop Docker services
	$(COMPOSE) down

docker-restart: ## Restart Docker services
	$(COMPOSE) restart

docker-ps: ## Show Docker service status
	$(COMPOSE) ps

docker-logs: ## Tail logs for all Docker services
	$(COMPOSE) logs -f

docker-logs-backend: ## Tail backend logs
	$(COMPOSE) logs -f backend

docker-logs-frontend: ## Tail frontend logs
	$(COMPOSE) logs -f frontend

docker-logs-db: ## Tail PostgreSQL logs
	$(COMPOSE) logs -f postgres

docker-shell-backend: ## Open shell inside backend container
	$(COMPOSE) exec backend sh

docker-shell-db: ## Open shell inside postgres container
	$(COMPOSE) exec postgres sh

docker-db-cli: ## Open psql inside postgres container
	$(COMPOSE) exec postgres sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

docker-migrate: ## Apply Alembic migrations inside backend container
	$(COMPOSE) exec backend python -m alembic upgrade head

docker-migration: ## Create Alembic migration inside backend container, use MSG=...
	$(COMPOSE) exec backend python -m alembic revision --autogenerate -m "$(MSG)"

backend-install: ## Install backend dependencies into current Python environment
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.txt

backend-dev: ## Run backend locally from the current Python environment
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --reload

backend-migrate: ## Apply Alembic migrations locally
	cd $(BACKEND_DIR) && $(PYTHON) -m alembic upgrade head

backend-test: ## Run backend unit tests locally
	cd $(BACKEND_DIR) && $(PYTHON) -m unittest discover -s tests -p 'test_*.py'

frontend-install: ## Install frontend dependencies
	cd $(FRONTEND_DIR) && $(NPM) install

frontend-dev: ## Run frontend locally
	cd $(FRONTEND_DIR) && $(NPM) run dev

frontend-lint: ## Run frontend lint
	cd $(FRONTEND_DIR) && $(NPM) run lint

lint: frontend-lint ## Run available lint commands

test: backend-test ## Run available automated tests

health: ## Check backend health endpoint
	curl -fsS http://localhost:8000/health && printf '\n'

docker-clean: ## Stop Docker services and remove volumes
	$(COMPOSE) down -v
