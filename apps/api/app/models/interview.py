import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, utc_now
from app.models.profile import ExperienceLevel

if TYPE_CHECKING:
    from app.models.question import Question
    from app.models.resume import Resume
    from app.models.user import User


class InterviewType(enum.StrEnum):
    TECHNICAL = "technical"
    CODING = "coding"
    SYSTEM_DESIGN = "system_design"


class InteractionMode(enum.StrEnum):
    TEXT = "text"
    VOICE = "voice"


class InterviewStatus(enum.StrEnum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    FAILED = "failed"


class TurnSpeaker(enum.StrEnum):
    ASSISTANT = "assistant"
    CANDIDATE = "candidate"


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_role: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    interview_type: Mapped[InterviewType] = mapped_column(
        Enum(InterviewType, name="interview_type_enum", native_enum=False),
        default=InterviewType.TECHNICAL,
        nullable=False,
    )
    interaction_mode: Mapped[InteractionMode] = mapped_column(
        Enum(InteractionMode, name="interaction_mode_enum", native_enum=False),
        default=InteractionMode.TEXT,
        nullable=False,
    )
    difficulty: Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel, name="experience_level_enum", native_enum=False),
        default=ExperienceLevel.INTERMEDIATE,
        nullable=False,
    )
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, name="interview_status_enum", native_enum=False),
        default=InterviewStatus.CREATED,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    resume: Mapped[Optional["Resume"]] = relationship("Resume")
    turns: Mapped[list["InterviewTurn"]] = relationship(
        "InterviewTurn",
        back_populates="session",
        order_by="InterviewTurn.sequence_number",
        cascade="all, delete-orphan",
    )


class InterviewTurn(Base):
    __tablename__ = "interview_turns"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence_number", name="uq_session_turn_sequence"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    speaker: Mapped[TurnSpeaker] = mapped_column(
        Enum(TurnSpeaker, name="turn_speaker_enum", native_enum=False),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    input_mode: Mapped[InteractionMode] = mapped_column(
        Enum(InteractionMode, name="interaction_mode_enum", native_enum=False),
        default=InteractionMode.TEXT,
        nullable=False,
    )
    turn_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    session: Mapped["InterviewSession"] = relationship("InterviewSession", back_populates="turns")
    question: Mapped[Optional["Question"]] = relationship("Question")
