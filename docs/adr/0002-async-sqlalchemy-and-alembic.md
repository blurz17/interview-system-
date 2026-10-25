# ADR 0002: Async SQLAlchemy 2.x and Alembic Migrations

## Status
Accepted

## Context
High-concurrency technical interviews involve long-lived WebSocket turns, live coding evaluations, and streaming inference. Synchronous ORM calls would block the FastAPI event loop during database I/O. Furthermore, schema evolution must be version-controlled, auditable, and reproducible across environments.

## Decision
- Use **SQLAlchemy 2.x** with the `asyncpg` async PostgreSQL driver.
- Use **Alembic** for all database migrations. Production and test environments must never rely on `Base.metadata.create_all()` for schema evolution on existing databases.
- Models inherit from a shared declarative base with UUID primary keys and UTC timezone-aware timestamps.
- Support a configurable connection string to allow in-memory SQLite / aiosqlite fallback during isolated unit tests and CI.

## Consequences
- **Positive**: Non-blocking I/O throughout FastAPI endpoints; reproducible schema migrations; strict schema consistency.
- **Negative**: Async session management requires explicit async context handling in FastAPI dependencies.
