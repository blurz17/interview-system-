# CareerPilot — Deployment Guide

## 1. Local Development Architecture
- **API Server**: FastAPI with Uvicorn (`http://localhost:8000`)
- **Frontend App**: Vite React Development Server (`http://localhost:5173`)
- **Database**: PostgreSQL 16+ on port `5432` (Docker Compose or local Windows service)
- **Code Execution**: Judge0 CE API on port `2358`

## 2. Running with Docker Compose
```bash
# Start PostgreSQL, API, and Web containers
docker compose up -d

# Check service health
docker compose ps
```

## 3. Production Considerations
- Set `DEBUG=false` and generate high-entropy secrets for `JWT_SECRET_KEY`.
- Run database migrations via Alembic: `alembic upgrade head`.
- Place FastAPI behind a reverse proxy (e.g., NGINX / Caddy) with TLS termination.
- Configure rate limits and quotas for AI and Judge0 integrations.
