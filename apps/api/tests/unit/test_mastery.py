import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mastery import AssignmentStatus, TrainingAssignment, UserSkillMastery
from app.models.profile import ExperienceLevel
from app.models.skill import Skill
from app.modules.skills.seed import seed_skills


@pytest.fixture(autouse=True)
async def seed_data(db_session: AsyncSession):
    await seed_skills(db_session)


@pytest.mark.asyncio
async def test_mastery_formula_and_evidence_updates(
    client: AsyncClient,
    db_session: AsyncSession,
):
    # 1. Register candidate
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "mastery_cand@example.edu", "password": "Password123!"},
    )
    assert reg.status_code == 201
    headers = {"Authorization": f"Bearer {reg.json()['tokens']['access_token']}"}

    # Fetch a skill (Python)
    skill_res = await db_session.execute(Skill.__table__.select().where(Skill.slug == "python"))
    python_skill = skill_res.first()
    assert python_skill is not None
    skill_id = python_skill.id

    # Create a training assignment for Python
    assignment = TrainingAssignment(
        user_id=uuid.UUID(reg.json()["user"]["id"]),
        skill_id=skill_id,
        title="Python Data Structures Drill",
        description="Practice dictionary lookups and list comprehensions.",
        exercise_type="coding",
        difficulty=ExperienceLevel.INTERMEDIATE,
        status=AssignmentStatus.PENDING,
    )
    db_session.add(assignment)
    await db_session.commit()
    await db_session.refresh(assignment)

    # 2. Submit first attempt with score = 80.0
    resp_att1 = await client.post(
        f"/api/v1/training/assignments/{assignment.id}/attempts",
        headers=headers,
        json={"score": 80.0, "result_summary": "Passed initial test cases."},
    )
    assert resp_att1.status_code == 201

    # Verify initial mastery score = 0.8
    resp_mastery1 = await client.get("/api/v1/skills/mastery", headers=headers)
    assert resp_mastery1.status_code == 200
    m_list1 = resp_mastery1.json()
    py_m1 = next(m for m in m_list1 if m["skill_slug"] == "python")
    assert pytest.approx(py_m1["mastery_score"], 0.01) == 0.80
    assert py_m1["evidence_count"] == 1

    # 3. Create another assignment and submit attempt with score = 100.0
    # M_new = (1 - 0.3) * 0.8 + 0.3 * 1.0 = 0.56 + 0.30 = 0.86
    assignment2 = TrainingAssignment(
        user_id=uuid.UUID(reg.json()["user"]["id"]),
        skill_id=skill_id,
        title="Advanced Python Generators",
        description="Generators and memory efficiency.",
        exercise_type="coding",
        difficulty=ExperienceLevel.ADVANCED,
        status=AssignmentStatus.PENDING,
    )
    db_session.add(assignment2)
    await db_session.commit()

    resp_att2 = await client.post(
        f"/api/v1/training/assignments/{assignment2.id}/attempts",
        headers=headers,
        json={"score": 100.0, "result_summary": "Perfect execution."},
    )
    assert resp_att2.status_code == 201

    # Verify updated mastery score = 0.86
    resp_mastery2 = await client.get("/api/v1/skills/mastery", headers=headers)
    m_list2 = resp_mastery2.json()
    py_m2 = next(m for m in m_list2 if m["skill_slug"] == "python")
    assert pytest.approx(py_m2["mastery_score"], 0.01) == 0.86
    assert py_m2["evidence_count"] == 2


@pytest.mark.asyncio
async def test_recommendation_generator_and_prerequisites(
    client: AsyncClient,
    db_session: AsyncSession,
):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "prereq_cand@example.edu", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['tokens']['access_token']}"}
    user_id = uuid.UUID(reg.json()["user"]["id"])

    # Locate SQL skills
    sql_fund = (await db_session.execute(Skill.__table__.select().where(Skill.slug == "sql"))).first()
    indexing = (await db_session.execute(Skill.__table__.select().where(Skill.slug == "indexing-optimization"))).first()
    assert sql_fund is not None and indexing is not None

    # Simulate weak indexing score (0.45) with unready prerequisite (sql-fundamentals not yet assessed)
    weak_indexing = UserSkillMastery(
        user_id=user_id,
        skill_id=indexing.id,
        mastery_score=0.45,
        confidence=0.7,
        evidence_count=1,
    )
    db_session.add(weak_indexing)
    await db_session.commit()

    # Call recommendations generation
    resp_gen = await client.post("/api/v1/training/assignments/generate", headers=headers)
    assert resp_gen.status_code == 200
    assignments = resp_gen.json()
    assert len(assignments) > 0

    # Verify that SQL Fundamentals (prerequisite) is recommended because prerequisite is needed!
    titles = [a["title"] for a in assignments]
    assert any("SQL" in t for t in titles)
