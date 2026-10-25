import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.skills.seed import seed_skills


@pytest.fixture(autouse=True)
async def seed_test_skills(db_session: AsyncSession):
    await seed_skills(db_session)


@pytest.mark.asyncio
async def test_list_skills(client: AsyncClient):
    response = await client.get("/api/v1/skills")
    assert response.status_code == 200
    skills = response.json()
    assert len(skills) > 0
    slugs = [s["slug"] for s in skills]
    assert "python" in slugs
    assert "sql" in slugs
    assert "dynamic-programming" in slugs


@pytest.mark.asyncio
async def test_filter_skills_by_category(client: AsyncClient):
    response = await client.get("/api/v1/skills?category=databases")
    assert response.status_code == 200
    skills = response.json()
    assert len(skills) >= 2
    for s in skills:
        assert s["category"] == "databases"


@pytest.mark.asyncio
async def test_get_skill_with_prerequisites(client: AsyncClient):
    list_res = await client.get("/api/v1/skills")
    dp_skill = next(s for s in list_res.json() if s["slug"] == "dynamic-programming")

    response = await client.get(f"/api/v1/skills/{dp_skill['id']}")
    assert response.status_code == 200
    skill = response.json()
    assert skill["slug"] == "dynamic-programming"
    assert len(skill["prerequisites"]) > 0
    prereq_slugs = [p["slug"] for p in skill["prerequisites"]]
    assert "recursion-backtracking" in prereq_slugs
