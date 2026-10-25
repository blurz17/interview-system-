import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.mastery import AssignmentStatus


class UserSkillMasteryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    skill_slug: str
    category: str
    mastery_score: float
    confidence: float
    evidence_count: int
    last_assessed_at: datetime


class TrainingAssignmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    title: str
    description: str
    exercise_type: str
    difficulty: str
    status: AssignmentStatus
    created_at: datetime
    completed_at: datetime | None = None


class TrainingAttemptCreate(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    result_summary: str = Field(..., min_length=1, max_length=2000)


class TrainingAttemptPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assignment_id: uuid.UUID
    user_id: uuid.UUID
    score: float
    result_summary: str
    completed_at: datetime


class TrainingSolveRequest(BaseModel):
    candidate_answer: str = Field(..., min_length=3, max_length=5000)


class TrainingSolveResponse(BaseModel):
    assignment_id: uuid.UUID
    score: float
    feedback: str
    strengths: list[str] = []
    improvements: list[str] = []
    new_mastery_score: float
