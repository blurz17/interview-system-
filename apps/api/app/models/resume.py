import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.resume_skill import ResumeSkill
    from app.models.user import User


class ParsingStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

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
    storage_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    file_content: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )
    parsed_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    parsing_status: Mapped[ParsingStatus] = mapped_column(
        Enum(ParsingStatus, name="parsing_status_enum", native_enum=False),
        default=ParsingStatus.PENDING,
        nullable=False,
    )
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus, name="extraction_status_enum", native_enum=False),
        default=ExtractionStatus.PENDING,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    skills: Mapped[list["ResumeSkill"]] = relationship(
        "ResumeSkill",
        back_populates="resume",
        cascade="all, delete-orphan",
    )
