import enum
import uuid
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, utc_now
from app.models.profile import ExperienceLevel

if TYPE_CHECKING:
    from app.models.coding import QuestionTestCase
    from app.models.skill import Skill


class QuestionType(enum.StrEnum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type_enum", native_enum=False),
        default=QuestionType.TECHNICAL,
        nullable=False,
    )
    difficulty: Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel, name="experience_level_enum", native_enum=False),
        default=ExperienceLevel.INTERMEDIATE,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_role: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    expected_answer_criteria: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    starter_code: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    solution_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    skill: Mapped[Optional["Skill"]] = relationship("Skill")
    test_cases: Mapped[list["QuestionTestCase"]] = relationship(
        "QuestionTestCase",
        back_populates="question",
        cascade="all, delete-orphan",
    )
