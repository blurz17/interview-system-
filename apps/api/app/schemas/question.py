import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.profile import ExperienceLevel
from app.models.question import QuestionType


class QuestionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    prompt: str
    question_type: QuestionType
    difficulty: ExperienceLevel
    category: str
    target_role: str | None = None
    starter_code: str | None = None
    created_at: datetime


class QuestionCreate(BaseModel):
    title: str
    prompt: str
    question_type: QuestionType = QuestionType.TECHNICAL
    difficulty: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    category: str
    skill_slug: str | None = None
    target_role: str | None = None
    expected_answer_criteria: list[dict[str, Any]] | None = None
    starter_code: str | None = None
    solution_explanation: str | None = None
