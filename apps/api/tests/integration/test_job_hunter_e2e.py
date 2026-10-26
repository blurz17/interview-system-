import pytest
import io
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_job_hunter_full_authenticated_e2e_flow(client: AsyncClient):
    """
    End-to-End Test:
    1. Register new candidate
    2. Log in and get JWT token
    3. Upload CV file (multipart/form-data)
    4. Fetch job details from URL
    5. Run Job Hunter fit analysis on the uploaded CV against the job
    6. Validate response contract, score bounds, and recommendation structures
    """
    email = "e2e_candidate@example.com"
    password = "SecureCandidatePass123!"

    # 1. Register candidate
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "E2E Hunter Tester"
        }
    )
    assert reg_res.status_code in [201, 400]

    # 2. Login to get token
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert login_res.status_code == 200
    token = login_res.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Upload CV file
    sample_cv_content = b"""
    Ahmed Abdelrahman - Backend Developer
    Location: Egypt | Email: e2e_candidate@example.com
    Technical Skills: Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Celery, Redis, Docker, Pytest, Linux
    Projects:
    - Built scalable real-time backend with FastAPI, PostgreSQL and Redis.
    - Implemented background queues with Celery and database migrations with Alembic.
    - Wrote comprehensive test suites with Pytest.
    """
    files = {
        "file": ("candidate_cv.txt", io.BytesIO(sample_cv_content), "text/plain")
    }
    upload_res = await client.post("/api/v1/resumes", files=files, headers=headers)
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["id"]

    # 4. Fetch Job from LinkedIn URL
    fetch_res = await client.post(
        "/api/v1/job-hunter/fetch-job",
        json={"url": "https://www.linkedin.com/jobs/view/4479952015/"}
    )
    assert fetch_res.status_code == 200
    job_data = fetch_res.json()
    assert "title" in job_data
    assert "description" in job_data
    assert len(job_data["description"]) > 100

    # 5. Run Job Hunter Analysis linking the resume_id
    analyze_res = await client.post(
        "/api/v1/job-hunter/analyze",
        data={
            "resume_id": resume_id,
            "job_url": "https://www.linkedin.com/jobs/view/4479952015/"
        },
        headers=headers
    )
    assert analyze_res.status_code == 200
    result = analyze_res.json()

    # 6. Deep Schema & Rubric Assertions
    assert "overall_match_score" in result
    assert 0 <= result["overall_match_score"] <= 100
    assert "verdict" in result
    assert "location_eligible" in result
    assert "timezone_eligible" in result
    assert isinstance(result["hard_requirements_analysis"], list)
    assert len(result["hard_requirements_analysis"]) > 0
    assert isinstance(result["tailored_cv_bullets_to_add"], list)
    assert len(result["tailored_cv_bullets_to_add"]) > 0
    assert isinstance(result["recruiter_outreach_message"], str)
    assert len(result["recruiter_outreach_message"]) > 50


@pytest.mark.asyncio
async def test_job_hunter_anonymous_direct_text_analysis(client: AsyncClient):
    """
    Integration Test:
    Allows anonymous or unauthenticated users to test CV text against job text.
    """
    data = {
        "cv_text": "Python Engineer with Docker and Linux.",
        "job_text": "Looking for Python Developer with Docker and Linux expertise in remote setting."
    }
    res = await client.post("/api/v1/job-hunter/analyze", data=data)
    assert res.status_code == 200
    result = res.json()
    assert result["overall_match_score"] >= 30
    assert len(result["hard_requirements_analysis"]) > 0
