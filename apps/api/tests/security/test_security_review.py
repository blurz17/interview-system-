import io
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import QuestionTestCase
from app.models.profile import ExperienceLevel
from app.models.question import Question, QuestionType
from app.models.skill import Skill


@pytest.mark.asyncio
async def test_candidate_safe_hidden_test_cases_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Rule 4 & 6: Hidden test cases must NEVER expose input_data, expected_output, or actual_output

    to the candidate under any circumstances.
    """
    # 1. Setup skill & question with hidden test case
    sk = Skill(
        slug="security-py",
        name="Security Python",
        description="Testing security bounds",
        category="languages",
        difficulty_level=ExperienceLevel.BEGINNER,
        is_active=True,
    )
    db_session.add(sk)
    await db_session.flush()

    q = Question(
        title="Hidden Secret Question",
        prompt="Secret question prompt",
        question_type=QuestionType.CODING,
        difficulty=ExperienceLevel.BEGINNER,
        category="security",
        skill_id=sk.id,
        is_active=True,
    )
    db_session.add(q)
    await db_session.flush()

    secret_input = "SECRET_CANDIDATE_INPUT_42"
    secret_output = "SECRET_EXPECTED_RESULT_99"

    tc_pub = QuestionTestCase(
        question_id=q.id,
        input_data="public_input",
        expected_output="public_output",
        is_hidden=False,
    )
    tc_hidden = QuestionTestCase(
        question_id=q.id,
        input_data=secret_input,
        expected_output=secret_output,
        is_hidden=True,
    )
    db_session.add_all([tc_pub, tc_hidden])
    await db_session.commit()

    # Register user
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "hiddencase@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create & start interview
    sess_res = await client.post(
        "/api/v1/interviews",
        headers=headers,
        json={"target_role": "Backend", "interview_type": "coding", "difficulty": "beginner"},
    )
    session_id = sess_res.json()["id"]
    await client.post(f"/api/v1/interviews/{session_id}/start", headers=headers)

    # Submit solution
    sub_res = await client.post(
        f"/api/v1/interviews/{session_id}/submissions",
        headers=headers,
        json={
            "question_id": str(q.id),
            "language_id": 71,
            "source_code": "def solution():\n    return 'secret'\n",
        },
    )
    assert sub_res.status_code == 201
    sub_id = sub_res.json()["id"]

    # Query results endpoint
    results_res = await client.get(
        f"/api/v1/submissions/{sub_id}/results",
        headers=headers,
    )
    assert results_res.status_code == 200
    results = results_res.json()
    assert len(results) == 2

    for r in results:
        if r["is_hidden"]:
            # Neither input nor expected/actual output must contain the secret strings
            assert r["input_data"] is None or secret_input not in r["input_data"]
            assert r["expected_output"] is None or secret_output not in r["expected_output"]
            assert r["actual_output"] is None or secret_output not in r["actual_output"]
        else:
            assert r["input_data"] == "public_input"
            assert r["expected_output"] == "public_output"


@pytest.mark.asyncio
async def test_oversized_payload_protection(client: AsyncClient):
    """Rule: Bounded payload sizes.

    Oversized resumes (>10MB), audio (>10MB), or source code (>50KB) must be rejected safely.
    """
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "payload_bounds@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Oversized resume (11 MB)
    large_resume_bytes = b"x" * (11 * 1024 * 1024)
    res_large_cv = await client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": ("large_cv.txt", io.BytesIO(large_resume_bytes), "text/plain")},
    )
    assert res_large_cv.status_code in (400, 413)

    # 2. Oversized audio (11 MB)
    large_audio_bytes = b"x" * (11 * 1024 * 1024)
    res_large_audio = await client.post(
        "/api/v1/voice/transcriptions",
        headers=headers,
        files={"file": ("large_audio.wav", io.BytesIO(large_audio_bytes), "audio/wav")},
    )
    assert res_large_audio.status_code in (400, 413)

    # 3. Oversized code submission (>50,000 characters)
    oversized_code = "print(1)\n" * 7000  # ~63,000 chars
    res_code = await client.post(
        f"/api/v1/interviews/{uuid.uuid4()}/submissions",
        headers=headers,
        json={"question_id": str(uuid.uuid4()), "language_id": 71, "source_code": oversized_code},
    )
    assert res_code.status_code == 422


@pytest.mark.asyncio
async def test_invalid_mime_types_rejected(client: AsyncClient):
    """Unsupported MIME types for resume or voice must be rejected with 400 Bad Request."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "mime_test@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload an executable as a resume
    res_bad_cv = await client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": ("malicious.exe", io.BytesIO(b"MZ...fake_binary"), "application/x-msdownload")},
    )
    assert res_bad_cv.status_code == 400

    # Upload non-audio file as voice recording
    res_bad_audio = await client.post(
        "/api/v1/voice/transcriptions",
        headers=headers,
        files={"file": ("script.py", io.BytesIO(b"print('hello')"), "text/x-python")},
    )
    assert res_bad_audio.status_code == 400
