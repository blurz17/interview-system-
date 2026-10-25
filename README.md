# CareerPilot

AI-Powered Technical Interview Training Platform for Computer Science Students & Recent Graduates.

CareerPilot provides interactive interview training combining adaptive AI interviewers, live Monaco coding execution via Judge0, evidence-based rubric evaluation, and a deterministic **Skill Mastery Engine** that diagnoses knowledge gaps and recommends targeted exercises.

---

## Architecture Overview

CareerPilot is structured as a **modular monolith** monorepo:

- **`apps/api`**: FastAPI backend (Python 3.12, SQLAlchemy 2.x async, Alembic, Pydantic v2, PostgreSQL / pgvector).
- **`apps/web`**: React 18 / Vite / TypeScript single-page application (Tailwind CSS, TanStack Query, React Hook Form, Monaco Editor).
- **`docs/`**: Comprehensive specifications, architecture decision records (ADRs), ERD, API contracts, and security guides.

---

## Quickstart

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- PostgreSQL 16+ (Local service or Docker Compose)

### 1. Environment Setup
Copy the environment template and adjust values:
```bash
cp .env.example .env
```

### 2. Backend Setup
```bash
cd apps/api
# Recommended: Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -e ".[dev]"
```

Run backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Liveness: `http://localhost:8000/health/live`
- Health Readiness: `http://localhost:8000/health/ready`

### 3. Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Testing

```bash
# Backend tests
cd apps/api
pytest tests/ -v

# Frontend tests
cd apps/web
npm run test:run
```
