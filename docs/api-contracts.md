# CareerPilot — API Contracts & Conventions

## 1. Conventions
- Base Path: `/api/v1`
- Request/Response Format: UTF-8 JSON
- Date/Time: ISO 8601 UTC strings (`YYYY-MM-DDTHH:MM:SSZ`)
- IDs: Standard UUID v4 strings

## 2. Standard Error Envelope
```json
{
  "error": {
    "code": "SESSION_NOT_ACTIVE",
    "message": "This interview session is no longer active.",
    "request_id": "4b684cb6-5c5e-4c2c-9828-56839ebf85eb"
  }
}
```

## 3. Core Endpoint Endpoints Summary
| Module | Method | Route | Description |
|---|---|---|---|
| Health | GET | `/health/live` | Application liveness probe |
| Health | GET | `/health/ready` | Database readiness probe |
| Auth | POST | `/api/v1/auth/register` | Register new candidate account |
| Auth | POST | `/api/v1/auth/login` | Authenticate with credentials |
| Auth | POST | `/api/v1/auth/refresh` | Rotate access and refresh tokens |
| Auth | POST | `/api/v1/auth/logout` | Revoke current refresh token |
| Auth | GET | `/api/v1/auth/me` | Current user profile |
| Profiles | GET / PUT | `/api/v1/profile` | Candidate profile management |
| Resumes | POST | `/api/v1/resumes` | Upload CV |
| Resumes | GET / PATCH | `/api/v1/resumes/{id}/skills` | Retrieve and review extracted skills |
| Interviews | POST | `/api/v1/interviews` | Create interview session |
| Interviews | POST | `/api/v1/interviews/{id}/turns` | Submit response & get next turn |
| Coding | POST | `/api/v1/interviews/{id}/submissions` | Submit code for Judge0 execution |
| Reports | GET | `/api/v1/interviews/{id}/report` | Versioned evaluation report |
| Training | GET / POST | `/api/v1/training/assignments` | Targeted assignments from Skill Engine |
| Voice | POST | `/api/v1/voice/transcriptions` | Bounded audio transcription |
