# CareerPilot — Development Guide

## 1. Monorepo Organization
```text
careerpilot/
├── apps/
│   ├── api/          # FastAPI backend modular monolith
│   └── web/          # React + Vite + Tailwind frontend
├── docs/             # Architecture, ADRs, schema, and API specs
├── storage/          # Local file uploads (gitignored)
├── .env.example      # Environment template
└── docker-compose.yml
```

## 2. Coding Conventions
- **Backend**: Python 3.12, strict type annotations, Pydantic v2 schemas, SQLAlchemy 2.0 async syntax, 100 character line length (enforced by Ruff).
- **Frontend**: TypeScript strict mode, functional React components with hooks, Tailwind utility styling, no inline styles.
- **Commits & State**: Incremental, phase-by-phase implementation. Each phase must pass linting and automated tests before advancing.
