.PHONY: help install lint test dev dev-api dev-web db-migrate db-seed

help:
	@echo "CareerPilot Makefile Commands:"
	@echo "  make install     - Install dependencies for both backend and frontend"
	@echo "  make dev         - Run both backend and frontend servers"
	@echo "  make dev-api     - Run FastAPI backend server"
	@echo "  make dev-web     - Run Vite frontend server"
	@echo "  make test        - Run backend and frontend tests"
	@echo "  make lint        - Run linters and typechecks"
	@echo "  make db-migrate  - Run Alembic migrations"
	@echo "  make db-seed     - Populate baseline demonstration dataset (skills & questions)"

install:
	cd apps/api && pip install -e ".[dev]"
	cd apps/web && npm install

dev-api:
	cd apps/api && uvicorn app.main:app --reload --port 8000

dev-web:
	cd apps/web && npm run dev

lint:
	cd apps/api && ruff check . && ruff format --check .
	cd apps/web && npm run typecheck

test:
	cd apps/api && pytest
	cd apps/web && npm run test:run

db-migrate:
	cd apps/api && alembic upgrade head

db-seed:
	cd apps/api && python -m app.db.seed
