# ADR 0001: Modular Monolith Architecture

## Status
Accepted

## Context
CareerPilot requires multiple core domains: Authentication, Candidate Profiles, CV Extraction, Questions & Interviews, Code Execution, Evaluation Reports, and the Skill Mastery Engine. While these domains have clear separation of responsibilities, early microservice decomposition introduces premature operational overhead, network latency, distributed transaction complexity, and synchronization friction.

## Decision
We adopt a **modular monolith** architecture:
- Single FastAPI application codebase located in `apps/api/app`.
- Explicit module boundaries (`app/modules/auth`, `app/modules/interviews`, `app/modules/skills`, etc.).
- Shared single PostgreSQL database as the primary source of truth.
- External capabilities (LLM, Embeddings, Speech, Judge0, File Storage) accessed through isolated adapter classes under `app/integrations/`.

## Consequences
- **Positive**: Simplified local development, transactional integrity across domains, easier end-to-end testing, zero distributed latency for inter-module calls.
- **Negative**: Requires strict module boundary discipline to prevent accidental tight coupling.
