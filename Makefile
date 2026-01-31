SHELL := /bin/bash

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

APP := app.main:app
PORT := 8000

.PHONY: help venv install run dev format-write lint test clean \
        db-up db-down db-reset db-logs db-supabase-schema db-supabase-import

help:
	@echo ""
	@echo "Targets:"
	@echo "  make venv       - create virtualenv"
	@echo "  make install    - install python deps from pyproject.toml"
	@echo "  make run        - run api (no reload)"
	@echo "  make dev        - run api with reload"
	@echo "  make format-write - format code (ruff)"
	@echo "  make lint       - lint code (ruff)"
	@echo "  make test       - run tests (pytest)"
	@echo "  make db-up      - start postgres (docker)"
	@echo "  make db-down    - stop postgres"
	@echo "  make db-reset   - wipe postgres volume (DANGEROUS)"
	@echo "  make db-logs    - tail postgres logs"
	@echo "  make db-supabase-schema - apply schema.sql to Supabase (uses SUPABASE_DATABASE_URL)"
	@echo "  make db-supabase-import - dump local data and import to Supabase (uses SUPABASE_DATABASE_URL)"
	@echo "  make clean      - remove venv + caches"
	@echo ""

venv:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@$(PIP) --version >/dev/null

install: venv
	@$(PIP) install --upgrade pip
	@$(PIP) install -e ".[dev]"

run: venv
	@$(UVICORN) $(APP) --host 0.0.0.0 --port $(PORT)

dev: venv
	@$(UVICORN) $(APP) --reload --host 0.0.0.0 --port $(PORT)

format-write: venv
	@$(VENV)/bin/ruff format .

lint: venv
	@$(VENV)/bin/ruff check .

test: install
	@$(VENV)/bin/pytest -q

db-up:
	@docker compose up -d db

db-down:
	@docker compose down

db-logs:
	@docker compose logs -f db

db-reset:
	@docker compose down -v
	@echo "Postgres volume removed."

db-psql:
	@docker exec -it cinelog-db psql -U app -d cinelog

db-schema:
	@docker exec -i cinelog-db psql -U app -d cinelog < schema.sql

db-supabase-schema:
	@set -a; source .env; set +a; \
	if [ -z "$$SUPABASE_DATABASE_URL" ]; then echo "SUPABASE_DATABASE_URL is not set in .env"; exit 1; fi; \
	psql "$$SUPABASE_DATABASE_URL" -f database/schema.sql

db-supabase-import:
	@set -a; source .env; set +a; \
	if [ -z "$$SUPABASE_DATABASE_URL" ]; then echo "SUPABASE_DATABASE_URL is not set in .env"; exit 1; fi; \
	if [ -n "$$LOCAL_DATABASE_URL" ]; then SRC="$$LOCAL_DATABASE_URL"; else SRC="postgresql://$$POSTGRES_USER:$$POSTGRES_PASSWORD@localhost:5432/$$POSTGRES_DB"; fi; \
	pg_dump "$$SRC" --data-only --column-inserts --no-owner --no-privileges > /tmp/cinelog_data.sql; \
	psql "$$SUPABASE_DATABASE_URL" -f /tmp/cinelog_data.sql

clean:
	@rm -rf $(VENV)
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -rf .pytest_cache .mypy_cache .ruff_cache
