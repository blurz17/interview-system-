import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.interview import InterviewSession
    from app.models.question import Question
    from app.models.user import User


class ExecutionStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestResultStatus(enum.StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    COMPILATION_ERROR = "compilation_error"
    RUNTIME_ERROR = "runtime_error"


class QuestionTestCase(Base):
    __tablename__ = "question_test_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input_data: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    expected_output: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    weight: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    question: Mapped["Question"] = relationship("Question", back_populates="test_cases")


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

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
    question_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    language_id: Mapped[int] = mapped_column(
        Integer,
        default=71,  # Python 3
        nullable=False,
    )
    source_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    execution_status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus, name="execution_status_enum", native_enum=False),
        default=ExecutionStatus.PENDING,
        nullable=False,
        index=True,
    )
    passed_tests: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_tests: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    runtime_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    memory_kb: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    session: Mapped["InterviewSession"] = relationship("InterviewSession")
    question: Mapped["Question"] = relationship("Question")
    user: Mapped["User"] = relationship("User")
    test_results: Mapped[list["TestResult"]] = relationship(
        "TestResult",
        back_populates="submission",
        cascade="all, delete-orphan",
    )


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("coding_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_case_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("question_test_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[TestResultStatus] = mapped_column(
        Enum(TestResultStatus, name="test_result_status_enum", native_enum=False),
        nullable=False,
    )
    actual_output: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    execution_time_ms: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    memory_kb: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    error_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    submission: Mapped["CodingSubmission"] = relationship("CodingSubmission", back_populates="test_results")
    test_case: Mapped["QuestionTestCase"] = relationship("QuestionTestCase")
