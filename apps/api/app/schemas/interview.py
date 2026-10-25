import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.interview import InteractionMode, InterviewStatus, InterviewType, TurnSpeaker
from app.models.profile import ExperienceLevel


class InterviewCreate(BaseModel):
    target_role: str = "Software Engineer (Backend)"
    interview_type: InterviewType = InterviewType.TECHNICAL
    interaction_mode: InteractionMode = InteractionMode.TEXT
    difficulty: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    resume_id: uuid.UUID | None = None


class InterviewTurnCreate(BaseModel):
    content: str
    input_mode: InteractionMode = InteractionMode.TEXT


class InterviewTurnPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sequence_number: int
    speaker: TurnSpeaker
    question_id: uuid.UUID | None = None
    content: str
    input_mode: InteractionMode
    turn_metadata: dict[str, Any] | None = None
    created_at: datetime


class InterviewPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target_role: str
    interview_type: InterviewType
    interaction_mode: InteractionMode
    difficulty: ExperienceLevel
    status: InterviewStatus
    resume_id: uuid.UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class InterviewDetail(InterviewPublic):
    turns: list[InterviewTurnPublic] = []
