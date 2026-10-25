import uuid

from pydantic import BaseModel, ConfigDict

from app.models.profile import ExperienceLevel


class SkillPrerequisitePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str


class SkillPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str | None = None
    category: str
    difficulty_level: ExperienceLevel
    is_active: bool
    prerequisites: list[SkillPrerequisitePublic] = []


class SkillCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    category: str
    difficulty_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    prerequisite_slugs: list[str] = []
