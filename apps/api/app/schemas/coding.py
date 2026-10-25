import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.coding import ExecutionStatus, TestResultStatus


class QuestionTestCaseBase(BaseModel):
    input_data: str
    expected_output: str
    is_hidden: bool = False
    weight: float = 1.0


class QuestionTestCaseCreate(QuestionTestCaseBase):
    pass


class QuestionTestCasePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    input_data: str | None = None
    expected_output: str | None = None
    is_hidden: bool
    weight: float
    created_at: datetime


class CodingSubmissionCreate(BaseModel):
    question_id: uuid.UUID
    language_id: int = Field(default=71, description="Judge0 language ID (e.g., 71 for Python)")
    source_code: str = Field(..., min_length=1, max_length=50000)
    idempotency_key: str | None = Field(default=None, max_length=100)


class TestResultPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test_case_id: uuid.UUID
    status: TestResultStatus
    is_hidden: bool = False
    input_data: str | None = None
    expected_output: str | None = None
    actual_output: str | None = None
    execution_time_ms: float | None = None
    memory_kb: float | None = None
    error_category: str | None = None
    created_at: datetime


class CodingSubmissionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    question_id: uuid.UUID
    user_id: uuid.UUID
    language_id: int
    source_code: str
    execution_status: ExecutionStatus
    passed_tests: int
    total_tests: int
    runtime_ms: float | None = None
    memory_kb: float | None = None
    submitted_at: datetime


class CodingSubmissionDetail(CodingSubmissionPublic):
    test_results: list[TestResultPublic] = []
