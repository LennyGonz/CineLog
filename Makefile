SHELL := /bin/bash

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

APP := app.main:app
PORT := 8000

.PHONY: help venv install run dev format-write lint test clean \
        db-up db-down db-reset db-logs

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

clean:
	@rm -rf $(VENV)
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@rm -rf .pytest_cache .mypy_cache .ruff_cache
