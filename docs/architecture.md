# CareerPilot — System Architecture

## 1. Overview
CareerPilot is an AI-powered technical interview training platform designed for computer science students and recent graduates. It features adaptive questioning, live code execution through Judge0, evidence-based rubric evaluation, and a deterministic **Skill Mastery Engine**.

## 2. Component Diagram

```mermaid
flowchart TB
    Browser["React + TypeScript (Vite, Tailwind, Monaco)"]
    API["FastAPI Modular Monolith"]

    subgraph Modules["Backend Modules"]
        Auth["Authentication & Security"]
        Profile["Profiles & CVs"]
        Interview["Interview Orchestrator"]
        Questions["Question Bank"]
        Coding["Coding & Execution"]
        Reports["Evaluations & Rubrics"]
        Skills["Skill Mastery Engine"]
        Providers["External Provider Adapters"]
    end

    DB[("PostgreSQL 16+ / pgvector")]
    Files["File Storage Adapter"]
    LLM["Hosted LLM (Qwen / HF)"]
    Embed["Embedding Provider (BGE)"]
    Speech["Speech Providers (Whisper / TTS)"]
    Judge["Judge0 CE Isolated Sandbox"]

    Browser -->|"REST / HTTPS"| API
    API --> Auth
    API --> Profile
    API --> Interview
    API --> Questions
    API --> Coding
    API --> Reports
    API --> Skills

    Auth --> DB
    Profile --> DB
    Profile --> Files
    Interview --> DB
    Questions --> DB
    Coding --> DB
    Reports --> DB
    Skills --> DB

    Interview --> Providers
    Questions --> Providers
    Reports --> Providers
    Skills --> Providers
    Coding --> Judge
    Providers --> LLM
    Providers --> Embed
    Providers --> Speech
```

## 3. Core Principles
1. **Explainable Skill Engine**: Explicit DAG prerequisite relationships and deterministic alpha-weighted mastery calculation.
2. **Untrusted Code Isolation**: Candidate code is executed only in Judge0 sandboxes with restricted network and resource bounds.
3. **Traceable Rubrics**: Every report score is backed by recorded evidence turns or flagged as insufficient evidence.
4. **Resilient Provider Fallback**: Text mode fallbacks when voice services or external APIs are unavailable.
