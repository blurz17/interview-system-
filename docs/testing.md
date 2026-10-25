# CareerPilot — Testing Strategy

## 1. Test Pyramid
1. **Backend Unit Tests**: Pytest testing individual utility functions, Argon2id hashing, token signing, schemas, and isolated endpoints.
2. **Backend Integration Tests**: Pytest using HTTPX AsyncClient and in-memory transactional database testing multi-step workflows.
3. **Backend Security Tests**: Dedicated tests asserting cross-user isolation and authorization boundaries.
4. **Frontend Unit & Component Tests**: Vitest + React Testing Library testing rendering, validation states, and API error states.
5. **End-to-End Tests**: Playwright testing complete candidate journey from registration to interview completion and training recommendations.

## 2. Test Execution Commands
```bash
# Run backend tests
cd apps/api
pytest tests/ -v

# Run frontend tests
cd apps/web
npm run test:run

# Run full linter and format validation
cd apps/api && ruff check . && ruff format --check .
cd apps/web && npm run typecheck
```
