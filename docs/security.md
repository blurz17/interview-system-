# CareerPilot — Security & Privacy Architecture

## 1. Authentication & Session Security
- **Argon2id Key Derivation**: All candidate passwords are hashed using memory-hard Argon2id (`argon2-cffi`). Plaintext passwords and password hashes are never logged or exposed in API response models.
- **JWT Architecture**:
  - Short-lived Access Tokens (15 minutes).
  - High-entropy Refresh Tokens stored in hashed SHA-256 form in `refresh_tokens`.
  - **Automatic Token Family Revocation**: Replaying an expired or already rotated refresh token revokes the entire token family, stopping compromise immediately.
- **Strict Server-Side Authorization**: Every protected endpoint enforces tenant isolation (`WHERE user_id = :current_user_id`). UUID unguessability is never relied upon for security.

---

## 2. Sandboxing Untrusted Code
- Candidate-submitted code is **strictly forbidden** from running in the FastAPI application process or directly on the host server.
- Code execution is delegated exclusively to **Judge0 CE** isolated worker containers with hard limits:
  - Max CPU wall clock: 5 seconds.
  - Max Memory: 256 MB.
  - Hard Egress Restriction: Isolated container networking (no external internet egress).
  - Deterministic fallback mock runner strictly performs static AST syntax compilation checks (`compile(code, ..., "exec")`) without executing bytecode.
- **Candidate-Safe Hidden Tests**: Hidden test case inputs, expected outputs, and actual execution outputs are permanently scrubbed from client responses to maintain assessment integrity.

---

## 3. Ephemeral Audio Privacy
- Raw candidate audio streams and uploaded audio recordings are treated as ephemeral data.
- Audio is processed in-memory or transient storage and **never** stored permanently on disk or in the database.
- Audio payloads are restricted to a 10MB maximum size and validated against explicit audio MIME types (`audio/wav`, `audio/webm`, `audio/mpeg`, etc.).
- Candidates have full preview and editing control over transcribed text before submitting turns.

---

## 4. Bounded Resource Limits & DoS Protections
- **CV Uploads**: Strict 10MB file limit with MIME validation (`application/pdf`, `text/plain`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`).
- **Code Submissions**: Maximum source code length restricted to 50,000 characters.
- **AI Turn Prompts**: Guardrails enforce character limits and system prompt encapsulation to prevent prompt injection.
- **Mastery Engine**: Update formula is bounded strictly between `[0.0, 1.0]`, preventing score explosion or decay anomalies.
