import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import CodingSubmission, ExecutionStatus
from app.models.interview import (
    InterviewSession,
    InterviewStatus,
    InterviewTurn,
    InterviewType,
    TurnSpeaker,
)
from app.modules.skills.seed import seed_skills


@pytest.fixture(autouse=True)
async def seed_data(db_session: AsyncSession):
    await seed_skills(db_session)


@pytest.mark.asyncio
async def test_generate_and_get_evaluation_report(
    client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Register candidate
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "eval_candidate@example.edu", "password": "Password123!"},
    )
    assert reg.status_code == 201
    token = reg.json()["tokens"]["access_token"]
    user_id = reg.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create and start session
    sess = InterviewSession(
        user_id=uuid.UUID(user_id),
        target_role="Software Engineer (Backend)",
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.IN_PROGRESS,
    )
    db_session.add(sess)
    await db_session.flush()

    # Add interview turns
    turn1 = InterviewTurn(
        session_id=sess.id,
        sequence_number=1,
        speaker=TurnSpeaker.ASSISTANT,
        content="Explain B-Tree indexing and when indexes can degrade performance.",
    )
    turn2 = InterviewTurn(
        session_id=sess.id,
        sequence_number=2,
        speaker=TurnSpeaker.CANDIDATE,
        content="B-Tree indexes provide logarithmic search times O(log N) for range and point lookups. However, every insert and update incurs disk I/O and tree rebalancing overhead.",
    )
    db_session.add_all([turn1, turn2])

    # Add a coding submission
    sub = CodingSubmission(
        session_id=sess.id,
        question_id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        language_id=71,
        source_code="def solution(): return True",
        execution_status=ExecutionStatus.COMPLETED,
        passed_tests=3,
        total_tests=3,
        runtime_ms=25.0,
        memory_kb=2048.0,
    )
    db_session.add(sub)
    await db_session.commit()

    # 3. Request evaluation report
    resp_report = await client.get(
        f"/api/v1/interviews/{sess.id}/report",
        headers=headers,
    )
    assert resp_report.status_code == 200
    report_data = resp_report.json()

    assert report_data["session_id"] == str(sess.id)
    assert report_data["rubric_version"] == "v1.0"
    assert report_data["overall_score"] >= 60.0
    assert len(report_data["strengths"]) > 0
    assert len(report_data["recommendations"]) > 0
    assert len(report_data["skill_evidences"]) > 0

    first_evidence = report_data["skill_evidences"][0]
    assert first_evidence["confidence"] >= 0.7
    assert "explanation" in first_evidence
    report_id = report_data["id"]

    # 4. Verify idempotency: repeated request returns same report without duplicate rows
    resp_repeat = await client.get(
        f"/api/v1/interviews/{sess.id}/report",
        headers=headers,
    )
    assert resp_repeat.status_code == 200
    assert resp_repeat.json()["id"] == report_id


@pytest.mark.asyncio
async def test_cross_user_report_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    # Candidate A
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "eval_a@example.edu", "password": "Password123!"},
    )
    headers_a = {"Authorization": f"Bearer {reg_a.json()['tokens']['access_token']}"}

    # Candidate B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "eval_b@example.edu", "password": "Password123!"},
    )
    user_b_id = reg_b.json()["user"]["id"]

    sess_b = InterviewSession(
        user_id=uuid.UUID(user_b_id),
        target_role="Frontend Engineer",
        interview_type=InterviewType.TECHNICAL,
        status=InterviewStatus.COMPLETED,
    )
    db_session.add(sess_b)
    await db_session.commit()

    # Candidate A attempting to view Candidate B's evaluation report must be forbidden (403)
    resp = await client.get(
        f"/api/v1/interviews/{sess_b.id}/report",
        headers=headers_a,
    )
    assert resp.status_code == 403
