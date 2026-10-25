# CareerPilot

> **AI-Powered Technical Interview Training Platform for Computer Science Students & Recent Graduates**

CareerPilot provides interactive, evidence-based technical interview preparation. It bridges the gap between static practice problems and real technical interviews by combining adaptive AI interviewing, a live sandboxed Monaco coding workspace with Judge0 CE execution, objective rubric-based scoring, and a deterministic **Skill Mastery Engine** that diagnoses knowledge gaps and recommends targeted exercises.

---

## Architecture Overview

CareerPilot is structured as a **modular monolith** with clear separation of concerns:

- **`apps/api`**: FastAPI backend (Python 3.12, SQLAlchemy 2.x async, Alembic, Pydantic v2, PostgreSQL / pgvector).
  - Modular architecture following `tiangolo/full-stack-fastapi-template` best practices.
  - Layered structure: `app/api/v1/endpoints/`, `app/modules/`, `app/models/`, `app/schemas/`, and `app/integrations/`.
- **`apps/web`**: React 18 / TypeScript / Vite single-page application.
  - Feature-sliced architecture following `alan2207/bulletproof-react`.
  - Tailwind CSS, Lucide icons, TanStack Query, Monaco Editor (`@monaco-editor/react`), and Web Speech API.
- **`docs/`**: Complete specifications, Architecture Decision Records (ADRs), Entity-Relationship Diagrams (ERD), API contracts, and security architecture.

---

## Key Features

1. **Candidate Profile & Authentication**:
   - Secure Argon2id password hashing.
   - Short-lived JWT access tokens with rotating refresh tokens and automatic token family revocation upon reuse.
2. **CV Upload & Skill Catalog**:
   - Multi-format CV upload (PDF, TXT, DOCX) with 10MB bounds.
   - Automated skill and experience extraction mapped to a 20+ skill graph with DAG prerequisite dependencies.
3. **Adaptive AI Interview Orchestration**:
   - Strict interview state machine (`created -> in_progress -> completed/abandoned/failed`).
   - Adaptive follow-up turns grounded in candidate responses.
4. **Sandboxed Coding Workspace**:
   - Live Monaco Editor with syntax highlighting, indentation, and starter templates.
   - Sandboxed execution via Judge0 CE with hard resource limits (5s CPU time limit, 256MB memory).
   - Candidate-safe privacy: hidden test cases evaluate accuracy but redact inputs and outputs from candidate-visible responses.
5. **Traceable Evaluation Reports**:
   - Idempotent report generation governed by versioned rubrics (`v1.0`).
   - Objective score computation combining sandbox test results with dialogue analysis.
   - Every evaluation score links directly to an empirical evidence record.
6. **Skill Mastery Engine**:
   - Exponential moving average progression formula:  
     $$M_{\text{new}} = (1 - \alpha) M_{\text{old}} + \alpha S \quad (\alpha = 0.30)$$
   - Topological prerequisite verification before recommending advanced topics.
   - Generation and tracking of targeted training assignments.
7. **Voice Interaction**:
   - Dual-mode speech interaction: Native browser Web Speech API with backend Whisper / Hugging Face transcription fallback.
   - Ephemeral audio privacy: raw audio is never permanently stored on disk.

---

## Quickstart Guide

### Prerequisites
- **Python 3.12+**
- **Node.js 20+** & **npm**
- **PostgreSQL 16+** (Local service or Docker Compose)

---

### Step 1: Clone & Configure Environment

```bash
git clone https://github.com/your-username/careerpilot.git
cd careerpilot

# Create environment file from template
cp .env.example .env
```

Review `.env` and verify database credentials (default: `postgresql+asyncpg://blurz:blurz@localhost:5432/careerpilot`).

---

### Step 2: Database Migration & Baseline Dataset Seeding

```bash
# Navigate to backend and create virtual environment
cd apps/api
python -m venv .venv

# Activate virtual environment:
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# Install backend dependencies
pip install -e ".[dev]"

# Run database migrations to head
alembic upgrade head

# Populate demonstration dataset (skills, prerequisite DAGs, and coding questions)
python -m app.db.seed
```

---

### Step 3: Run Backend Server

```bash
# From apps/api with active virtual environment:
uvicorn app.main:app --reload --port 8000
```

- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **Liveness Probe**: `http://localhost:8000/health/live`
- **Readiness Probe**: `http://localhost:8000/health/ready`

---

### Step 4: Run Frontend Development Server

In a new terminal window:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Running with Docker Compose

To start PostgreSQL, Judge0, API, and Web containers together:

```bash
docker compose up -d
docker compose ps
```

---

## Verification & Testing Suite

Both backend and frontend feature automated test suites with high test coverage:

```bash
# 1. Backend Verification (38 tests: Unit, Security, and E2E Integration)
cd apps/api
pytest -v
ruff check .

# 2. Frontend Verification (Typecheck, 10 Vitest component tests, and Production Build)
cd apps/web
npm run typecheck
npm run test:run
npm run build
```

---

## Core API Endpoints

| Area | Method | Route | Description |
|---|---|---|---|
| **Auth** | `POST` | `/api/v1/auth/register` | Register candidate account |
| **Auth** | `POST` | `/api/v1/auth/login` | Log in and receive JWT token pair |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Rotate tokens with reuse detection |
| **Auth** | `GET` | `/api/v1/auth/me` | Current user & candidate profile |
| **Resumes** | `POST` | `/api/v1/resumes` | Upload CV & extract skills |
| **Resumes** | `GET` | `/api/v1/resumes` | List user's uploaded CVs |
| **Interviews** | `POST` | `/api/v1/interviews` | Configure new interview session |
| **Interviews** | `POST` | `/api/v1/interviews/{id}/start` | Initialize interview & get first turn |
| **Interviews** | `POST` | `/api/v1/interviews/{id}/turns` | Submit answer & receive AI response |
| **Interviews** | `POST` | `/api/v1/interviews/{id}/submissions` | Submit code for Judge0 execution |
| **Interviews** | `POST` | `/api/v1/interviews/{id}/complete` | Complete interview session |
| **Evaluations** | `POST` | `/api/v1/interviews/{id}/evaluate` | Generate rubric-based scorecard |
| **Evaluations** | `GET` | `/api/v1/interviews/{id}/report` | Retrieve report with evidence |
| **Mastery** | `GET` | `/api/v1/skills/mastery` | Retrieve candidate skill mastery DAG |
| **Training** | `GET` | `/api/v1/training/assignments` | Retrieve targeted assignments |
| **Training** | `POST` | `/api/v1/training/assignments/generate` | Auto-generate targeted gap exercises |
| **Voice** | `POST` | `/api/v1/voice/transcriptions` | Speech-to-text audio transcription |
| **Voice** | `POST` | `/api/v1/voice/speech` | Text-to-speech audio synthesis |

---

## Security & Privacy Architecture

- **Argon2id Password Hashing**: Memory-hard key derivation prevents GPU cracking.
- **Refresh Token Rotation & Family Revocation**: Replaying an expired or revoked token immediately revokes the entire token family.
- **Strict Server-Side Authorization**: Every protected endpoint queries by `WHERE user_id = :current_user_id`.
- **Untrusted Code Sandboxing**: Candidate code never runs on the application server. Code runs in restricted Judge0 containers with no egress networking and tight CPU/memory limits.
- **Candidate-Safe Hidden Tests**: Hidden test case inputs, expected outputs, and execution results are permanently scrubbed from client responses.
- **Audio Privacy**: Audio recordings are ephemeral and never permanently saved to disk.
