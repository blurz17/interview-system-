import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.resume import ExtractionStatus, ParsingStatus


class ResumeSkillPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    skill_slug: str
    category: str
    evidence_text: str | None = None
    extraction_confidence: float
    source_section: str | None = None


class ResumePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size_bytes: int
    parsing_status: ParsingStatus
    extraction_status: ExtractionStatus
    created_at: datetime
    skills: list[ResumeSkillPublic] = []


class ResumeSkillsUpdate(BaseModel):
    skill_slugs: list[str]
