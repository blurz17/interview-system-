import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_job_hunter_analyze_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        data = {
            "cv_text": "Experienced Python Backend Developer with FastAPI, PostgreSQL, Alembic, Celery, Redis, Docker, and Pytest.",
            "job_text": "Looking for a Backend Engineer with Python, FastAPI, PostgreSQL schema design, and Docker containerization."
        }
        res = await client.post("/api/v1/job-hunter/analyze", data=data)
        assert res.status_code == 200
        payload = res.json()
        assert "overall_match_score" in payload
        assert payload["overall_match_score"] > 60
        assert "hard_requirements_analysis" in payload
        assert "tailored_cv_bullets_to_add" in payload
        assert "recruiter_outreach_message" in payload


@pytest.mark.asyncio
async def test_job_hunter_missing_inputs():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        res = await client.post("/api/v1/job-hunter/analyze", data={})
        assert res.status_code == 400
