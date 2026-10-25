# CareerPilot — Product Requirements Document (PRD)

## 1. Problem Statement
Computer science students and recent graduates preparing for software engineering technical interviews often rely on static problem lists or disjointed tools. They lack:
1. Realistic interactive interviews with technical follow-ups.
2. An integrated sandbox for verified code execution and runtime benchmarking.
3. Traceable, evidence-backed rubric evaluations rather than generic praise or criticism.
4. A personalized **Skill Mastery Engine** that maintains an evolving model of candidate competence, detects prerequisite gaps, and assigns targeted practice.

## 2. Target Persona
- **Primary**: Undergraduate and postgraduate computer science students and entry-level engineering applicants.
- **Goals**: Practice technical concepts, improve live coding under test-case constraints, and address specific concept weaknesses.

## 3. Product Scope
### In Scope (V1)
- User registration, authentication, JWT rotation, and profile management.
- CV upload (PDF/DOCX/TXT), secure storage, and structured skill extraction with user review.
- Role-based and difficulty-based technical interview setup.
- Dual-mode interaction: text-based and voice-transcribed conversation.
- Live Monaco code editor with Judge0 isolated sandbox execution and test-case evaluation.
- Structured evaluation reports with rubric versioning and traceable evidence items.
- Deterministic Skill Mastery Engine tracking skill DAG prerequisites and updating mastery scores via exponential smoothing.
- Targeted training assignments and reassessment cycles.

### Out of Scope (V1)
- Photorealistic avatar rendering.
- Emotion or gaze-based dishonesty detection.
- Training proprietary LLM foundation weights from scratch.
- Job recruiter boards and applicant tracking systems (ATS).
