# CareerPilot — Security and Privacy Architecture

## 1. Authentication & Session Security
- **Argon2id**: All passwords hashed using memory-hard Argon2id. Passwords are never logged or returned in responses.
- **JWT Architecture**: Short-lived access tokens (15 minutes). Rotating refresh tokens stored in hashed form in the database with automatic token family revocation upon reuse.
- **Authorization**: Every resource endpoint strictly enforces tenant ownership checks (`WHERE user_id = :current_user_id`). UUID unguessability is never relied upon for authorization.

## 2. Sandboxing Untrusted Code
- Candidate submitted source code is **never** executed inside the application process or on the host server.
- Code execution is delegated exclusively to **Judge0 CE** containers with hard limits:
  - Max CPU wall clock: 5 seconds.
  - Max RAM: 256 MB.
  - Disabled container networking (no egress traffic).
  - Sanitized runtime output.

## 3. Prompt Injection Defense
- Candidate CV texts and responses are treated as untrusted user data.
- System prompts are sealed with structural delimiter protections and explicit negative constraints.
- LLM outputs are validated against strict Pydantic schemas before any state update.

## 4. Privacy & Telemetry
- Raw audio streams are never stored by default; only transcripts submitted by the candidate are recorded.
- No biometric, facial, or emotional surveillance is performed.
