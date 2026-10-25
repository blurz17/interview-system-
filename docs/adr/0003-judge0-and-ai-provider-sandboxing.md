# ADR 0003: Sandboxed Code Execution and Untrusted Input Boundary

## Status
Accepted

## Context
Candidates submit arbitrary source code for execution during technical coding challenges. Candidate CVs and answers also contain untrusted text that is submitted to LLM prompts, introducing risks of code injection, resource exhaustion, and prompt injection attacks.

## Decision
1. **Never execute candidate code locally** inside the FastAPI process or host machine.
2. Delegate all code execution to **Judge0 CE** with strict execution wall time limits (5s), memory limits (256MB), and disabled host networking.
3. Treat candidate CV text and interview transcripts strictly as untrusted user data with prompt guards, length limits, and structured schema enforcement.
4. Keep provider credentials exclusively on the backend; the browser client never accesses Judge0 or LLM endpoints directly.

## Consequences
- **Positive**: Hard security boundary against remote code execution; protects infrastructure from malicious candidate submissions.
- **Negative**: Adds an external dependency on Judge0 API availability, requiring structured retry and timeout policies.
