import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.evaluation import EvaluationStatus


class SkillEvidencePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str | None = None
    skill_slug: str | None = None
    score: float
    evidence_type: str
    evidence_reference: str | None = None
    explanation: str
    confidence: float
    created_at: datetime


class EvaluationReportPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    overall_score: float
    rubric_version: str
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    evaluation_status: EvaluationStatus
    skill_evidences: list[SkillEvidencePublic] = []
    created_at: datetime
