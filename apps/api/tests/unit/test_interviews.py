import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.questions.seed import seed_questions
from app.modules.skills.seed import seed_skills


@pytest.fixture(autouse=True)
async def seed_data(db_session: AsyncSession):
    await seed_skills(db_session)
    await seed_questions(db_session)


@pytest.mark.asyncio
async def test_full_interview_lifecycle(client: AsyncClient):
    # 1. Register candidate
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "interview_candidate@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create interview session
    create_res = await client.post(
        "/api/v1/interviews",
        headers=headers,
        json={
            "target_role": "Backend Engineer",
            "interview_type": "technical",
            "interaction_mode": "text",
            "difficulty": "intermediate",
        },
    )
    assert create_res.status_code == 201
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["status"] == "created"

    # 3. Start interview session -> Turn 1
    start_res = await client.post(f"/api/v1/interviews/{session_id}/start", headers=headers)
    assert start_res.status_code == 200
    turn1 = start_res.json()
    assert turn1["sequence_number"] == 1
    assert turn1["speaker"] == "assistant"
    assert len(turn1["content"]) > 20
    assert turn1["turn_metadata"]["question_number"] == 1

    # Cannot restart an already started session
    restart_res = await client.post(f"/api/v1/interviews/{session_id}/start", headers=headers)
    assert restart_res.status_code == 400

    # 4. Candidate answers Question 1 -> Turn 2 candidate, Turn 3 assistant
    answer1_res = await client.post(
        f"/api/v1/interviews/{session_id}/turns",
        headers=headers,
        json={
            "content": "B-Tree indexes maintain sorted keys and provide logarithmic time lookups."
        },
    )
    assert answer1_res.status_code == 200
    turn3 = answer1_res.json()
    assert turn3["sequence_number"] == 3
    assert turn3["speaker"] == "assistant"
    assert len(turn3["content"]) > 20
    assert turn3["turn_metadata"]["question_number"] == 2

    # 5. Candidate answers Question 2 -> Turn 4 candidate, Turn 5 assistant
    answer2_res = await client.post(
        f"/api/v1/interviews/{session_id}/turns",
        headers=headers,
        json={
            "content": "In Read Committed, non-repeatable reads can occur because data is not locked."
        },
    )
    assert answer2_res.status_code == 200
    turn5 = answer2_res.json()
    assert turn5["sequence_number"] == 5
    assert turn5["speaker"] == "assistant"
    assert len(turn5["content"]) > 20
    assert turn5["turn_metadata"]["question_number"] == 3

    # 6. Candidate answers Question 3 -> Turn 6 candidate, Turn 7 concluding assistant turn
    answer3_res = await client.post(
        f"/api/v1/interviews/{session_id}/turns",
        headers=headers,
        json={
            "content": "The GIL ensures memory safety in CPython by restricting execution to one thread."
        },
    )
    assert answer3_res.status_code == 200
    turn7 = answer3_res.json()
    assert turn7["sequence_number"] == 7
    assert turn7["speaker"] == "assistant"
    assert turn7["turn_metadata"]["is_final"] is True

    # 7. Check interview detail & turns order
    detail_res = await client.get(f"/api/v1/interviews/{session_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["turns"]) == 7
    speakers = [t["speaker"] for t in detail["turns"]]
    assert speakers == [
        "assistant",
        "candidate",
        "assistant",
        "candidate",
        "assistant",
        "candidate",
        "assistant",
    ]

    # 8. Complete session
    comp_res = await client.post(f"/api/v1/interviews/{session_id}/complete", headers=headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "completed"

    # Cannot submit turn to a completed session
    rejected_turn = await client.post(
        f"/api/v1/interviews/{session_id}/turns",
        headers=headers,
        json={"content": "Extra answer after completion"},
    )
    assert rejected_turn.status_code == 400


@pytest.mark.asyncio
async def test_cross_user_interview_isolation(client: AsyncClient):
    # Candidate A creates session
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "candidate_a@university.edu", "password": "Password123!"},
    )
    token_a = reg_a.json()["tokens"]["access_token"]
    session_res = await client.post(
        "/api/v1/interviews",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"target_role": "Backend Engineer"},
    )
    session_id = session_res.json()["id"]

    # Candidate B tries to access Candidate A's session
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "candidate_b@university.edu", "password": "Password123!"},
    )
    token_b = reg_b.json()["tokens"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    get_res = await client.get(f"/api/v1/interviews/{session_id}", headers=headers_b)
    assert get_res.status_code == 403

    start_res = await client.post(f"/api/v1/interviews/{session_id}/start", headers=headers_b)
    assert start_res.status_code == 403
