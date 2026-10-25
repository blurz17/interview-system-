# CareerPilot — API Contracts & Conventions

## 1. Conventions
- **Base Path**: `/api/v1`
- **Request / Response Format**: UTF-8 JSON
- **Date/Time**: ISO 8601 UTC strings (`YYYY-MM-DDTHH:MM:SSZ`)
- **IDs**: Standard UUID v4 strings
- **Authentication**: HTTP Bearer Header (`Authorization: Bearer <access_token>`)

---

## 2. Standard Error Envelope
All error responses from the API adhere to the structured error envelope:
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You do not have access to this resource.",
    "request_id": "4b684cb6-5c5e-4c2c-9828-56839ebf85eb"
  }
}
```

Standard Error Codes:
- `BAD_REQUEST` (400)
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `NOT_FOUND` (404)
- `CONFLICT` (409)
- `PAYLOAD_TOO_LARGE` (413)
- `UNPROCESSABLE_ENTITY` (422)
- `INTERNAL_SERVER_ERROR` (500)

---

## 3. Complete Endpoint Reference

### Authentication & Profiles
| Method | Route | Request Body | Response Status | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/register` | `UserRegister` | 201 Created | Register account & candidate profile |
| `POST` | `/api/v1/auth/login` | `UserLogin` | 200 OK | Authenticate & issue token pair |
| `POST` | `/api/v1/auth/refresh` | `TokenRefreshRequest` | 200 OK | Rotate tokens with reuse detection |
| `POST` | `/api/v1/auth/logout` | `TokenRefreshRequest` | 200 OK | Revoke active refresh token |
| `GET` | `/api/v1/auth/me` | None | 200 OK | Current user & candidate profile |
| `PATCH` | `/api/v1/auth/me` | `CandidateProfileUpdate` | 200 OK | Update profile preferences |

### Resumes & Skills Extraction
| Method | Route | Request Body | Response Status | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/resumes` | `multipart/form-data` | 201 Created | Upload CV (PDF/TXT/DOCX, max 10MB) |
| `GET` | `/api/v1/resumes` | None | 200 OK | List candidate resumes with extracted skills |
| `GET` | `/api/v1/resumes/{id}` | None | 200 OK | Retrieve resume details |
| `DELETE` | `/api/v1/resumes/{id}` | None | 204 No Content | Delete resume & extracted skills |
| `PUT` | `/api/v1/resumes/{id}/skills` | `ResumeSkillsUpdate` | 200 OK | Manually update extracted skills |

### Skills Catalog
| Method | Route | Request Body | Response Status | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/skills` | Query params (category) | 200 OK | Browse active technical skills |
| `GET` | `/api/v1/skills/{id}` | None | 200 OK | Skill detail with prerequisites |
| `GET` | `/api/v1/skills/mastery` | None | 200 OK | Current candidate mastery graph |

### Interview Orchestration
| Method | Route | Request Body | Response Status | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/interviews` | `InterviewCreate` | 201 Created | Create interview session (`status=created`) |
| `GET` | `/api/v1/interviews` | None | 200 OK | List past interview sessions |
| `GET` | `/api/v1/interviews/{id}` | None | 200 OK | Interview session details & turns |
| `POST` | `/api/v1/interviews/{id}/start` | None | 200 OK | Transition to `in_progress` & get opening turn |
| `POST` | `/api/v1/interviews/{id}/turns` | `InterviewTurnCreate` | 200 OK | Submit candidate response & get assistant follow-up |
| `POST` | `/api/v1/interviews/{id}/complete` | None | 200 OK | Transition session to `completed` |
| `POST` | `/api/v1/interviews/{id}/abandon` | None | 200 OK | Abandon session (`status=abandoned`) |

### Code Execution (Judge0 Sandbox)
| Method | Route | Request Body | Response Status | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/interviews/{id}/submissions` | `CodingSubmissionCreate` | 201 Created | Execute code against question test suite |
| `GET` | `/api/v1/submissions/{id}` | None | 200 OK | Submission execution stats & status |
| `GET` | `/api/v1/submissions/{id}/results` | None | 200 OK | Candidate-safe test results (hidden cases redacted) |

### Evaluation Reports
| Method | Route | Request Body | Response Status | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/interviews/{id}/evaluate` | None | 200 OK | Generate or recalculate rubric evaluation |
| `GET` | `/api/v1/interviews/{id}/report` | None | 200 OK | Retrieve evaluation scorecard & evidence |

### Skill Mastery & Training
| Method | Route | Request Body | Response Status | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/training/assignments` | Query params (status) | 200 OK | List targeted training assignments |
| `POST` | `/api/v1/training/assignments/generate` | Query params (limit) | 200 OK | Generate assignments targeting identified gaps |
| `GET` | `/api/v1/training/assignments/{id}` | None | 200 OK | Training assignment detail |
| `POST` | `/api/v1/training/assignments/{id}/attempts` | `TrainingAttemptCreate` | 201 Created | Record attempt & recompute mastery |

### Voice Interaction
| Method | Route | Request Body | Response Status | Description |
|---|---|---|---|---|
| `GET` | `/api/v1/voice/capabilities` | None | 200 OK | Voice provider availability & configuration |
| `POST` | `/api/v1/voice/transcriptions` | `multipart/form-data` | 200 OK | Transcribe bounded audio file (max 10MB) |
| `POST` | `/api/v1/voice/speech` | `TTSRequest` | 200 OK | Synthesize speech from text |
