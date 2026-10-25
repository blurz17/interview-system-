import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import QuestionTestCase
from app.models.interview import InterviewSession, InterviewStatus, InterviewType
from app.models.profile import ExperienceLevel
from app.models.question import Question, QuestionType


@pytest.mark.asyncio
async def test_full_coding_submission_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Register candidate and get token
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "coding_candidate@example.edu", "password": "Password123!"},
    )
    assert reg.status_code == 201
    token = reg.json()["tokens"]["access_token"]
    user_id = reg.json()["user"]["id"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Create a coding question with both public and hidden test cases
    q = Question(
        title="Two Sum Test Question",
        prompt="Find two indices that sum to target.",
        question_type=QuestionType.CODING,
        difficulty=ExperienceLevel.BEGINNER,
        category="algorithms",
        starter_code="def two_sum(nums, target):\n    pass\n",
        is_active=True,
    )
    db_session.add(q)
    await db_session.flush()

    # Public test case
    tc_public = QuestionTestCase(
        question_id=q.id,
        input_data="[2, 7, 11, 15]\n9",
        expected_output="[0, 1]",
        is_hidden=False,
        weight=1.0,
    )
    # Hidden test case
    tc_hidden = QuestionTestCase(
        question_id=q.id,
        input_data="[3, 3]\n6",
        expected_output="[0, 1]",
        is_hidden=True,
        weight=1.5,
    )
    db_session.add_all([tc_public, tc_hidden])

    # Create interview session
    sess = InterviewSession(
        user_id=uuid.UUID(user_id),
        target_role="Software Engineer (Backend)",
        interview_type=InterviewType.CODING,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(sess)
    await db_session.commit()
    await db_session.refresh(sess)

    # 2. Submit code
    solution_code = """def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
"""
    idempotency_key = f"idem-{uuid.uuid4()}"
    resp_submit = await client.post(
        f"/api/v1/interviews/{sess.id}/submissions",
        headers=auth_headers,
        json={
            "question_id": str(q.id),
            "language_id": 71,
            "source_code": solution_code,
            "idempotency_key": idempotency_key,
        },
    )
    assert resp_submit.status_code == 201
    data_submit = resp_submit.json()
    assert data_submit["passed_tests"] == 2
    assert data_submit["total_tests"] == 2
    assert data_submit["execution_status"] == "completed"
    submission_id = data_submit["id"]

    # 3. Test Idempotency: repeating request with same key returns identical record
    resp_idem = await client.post(
        f"/api/v1/interviews/{sess.id}/submissions",
        headers=auth_headers,
        json={
            "question_id": str(q.id),
            "language_id": 71,
            "source_code": solution_code,
            "idempotency_key": idempotency_key,
        },
    )
    assert resp_idem.status_code == 201
    assert resp_idem.json()["id"] == submission_id

    # 4. Get submission details
    resp_get = await client.get(
        f"/api/v1/submissions/{submission_id}",
        headers=auth_headers,
    )
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == submission_id

    # 5. Get candidate-safe results and verify hidden tests are redacted
    resp_results = await client.get(
        f"/api/v1/submissions/{submission_id}/results",
        headers=auth_headers,
    )
    assert resp_results.status_code == 200
    results = resp_results.json()
    assert len(results) == 2

    public_res = next(r for r in results if not r["is_hidden"])
    assert public_res["input_data"] == "[2, 7, 11, 15]\n9"
    assert public_res["expected_output"] == "[0, 1]"
    assert public_res["actual_output"] == "[0, 1]"

    hidden_res = next(r for r in results if r["is_hidden"])
    # Strictly redacted
    assert hidden_res["input_data"] is None
    assert hidden_res["expected_output"] is None
    assert hidden_res["actual_output"] is None
    assert hidden_res["status"] == "passed"


@pytest.mark.asyncio
async def test_cross_user_submission_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    # Candidate A
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "candidate_a@example.edu", "password": "Password123!"},
    )
    token_a = reg_a.json()["tokens"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Candidate B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "candidate_b@example.edu", "password": "Password123!"},
    )
    user_b_id = reg_b.json()["user"]["id"]

    other_sess = InterviewSession(
        user_id=uuid.UUID(user_b_id),
        target_role="Frontend Engineer",
        interview_type=InterviewType.CODING,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(other_sess)

    q = Question(
        title="Sample Question 2",
        prompt="Do something.",
        question_type=QuestionType.CODING,
        category="general",
        is_active=True,
    )
    db_session.add(q)
    await db_session.commit()

    # Candidate A attempting to submit to Candidate B's session must be forbidden (403)
    resp = await client.post(
        f"/api/v1/interviews/{other_sess.id}/submissions",
        headers=headers_a,
        json={
            "question_id": str(q.id),
            "language_id": 71,
            "source_code": "def solution(): pass",
        },
    )
    assert resp.status_code == 403
