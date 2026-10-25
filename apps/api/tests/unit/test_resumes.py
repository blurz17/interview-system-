import io

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.skills.seed import seed_skills


@pytest.fixture(autouse=True)
async def seed_test_skills(db_session: AsyncSession):
    await seed_skills(db_session)


@pytest.mark.asyncio
async def test_upload_and_extract_resume(client: AsyncClient):
    # 1. Register candidate
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "cv_candidate@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload sample CV
    sample_cv = """
    Jane Doe
    Software Engineering Graduate
    
    Technical Skills
    Languages: Python, Go, SQL, JavaScript
    Frameworks & Systems: RESTful API Design, Caching and Redis
    
    Experience
    Backend Developer Intern
    Built data pipelines and optimized SQL queries.
    """
    files = {"file": ("resume.txt", io.BytesIO(sample_cv.encode("utf-8")), "text/plain")}

    upload_res = await client.post("/api/v1/resumes", headers=headers, files=files)
    assert upload_res.status_code == 201
    data = upload_res.json()
    assert data["original_filename"] == "resume.txt"
    assert data["parsing_status"] == "completed"
    assert data["extraction_status"] == "completed"

    extracted_slugs = [s["skill_slug"] for s in data["skills"]]
    assert "python" in extracted_slugs
    assert "sql" in extracted_slugs
    assert "rest-apis" in extracted_slugs


@pytest.mark.asyncio
async def test_patch_confirmed_skills(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "patch_cv@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sample_cv = "Skills: Python"
    files = {"file": ("cv.txt", io.BytesIO(sample_cv.encode("utf-8")), "text/plain")}
    upload_res = await client.post("/api/v1/resumes", headers=headers, files=files)
    resume_id = upload_res.json()["id"]

    # Candidate confirms/overrides skills: add "sql" and "dynamic-programming"
    patch_res = await client.patch(
        f"/api/v1/resumes/{resume_id}/skills",
        headers=headers,
        json={"skill_slugs": ["python", "sql", "dynamic-programming"]},
    )
    assert patch_res.status_code == 200
    updated_slugs = [s["skill_slug"] for s in patch_res.json()["skills"]]
    assert set(updated_slugs) == {"python", "sql", "dynamic-programming"}


@pytest.mark.asyncio
async def test_cross_user_resume_access_forbidden(client: AsyncClient):
    # User A uploads CV
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "owner@university.edu", "password": "Password123!"},
    )
    token_a = reg_a.json()["tokens"]["access_token"]
    files = {"file": ("cv.txt", io.BytesIO(b"Skills: Python"), "text/plain")}
    upload_res = await client.post(
        "/api/v1/resumes", headers={"Authorization": f"Bearer {token_a}"}, files=files
    )
    resume_id = upload_res.json()["id"]

    # User B tries to view or delete User A's CV
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "attacker@university.edu", "password": "Password123!"},
    )
    token_b = reg_b.json()["tokens"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    get_res = await client.get(f"/api/v1/resumes/{resume_id}", headers=headers_b)
    assert get_res.status_code == 403

    del_res = await client.delete(f"/api/v1/resumes/{resume_id}", headers=headers_b)
    assert del_res.status_code == 403


@pytest.mark.asyncio
async def test_invalid_extension_rejected(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "invalid_ext@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]
    files = {
        "file": (
            "malware.exe",
            io.BytesIO(b"malicious executable"),
            "application/octet-stream",
        )
    }

    res = await client.post(
        "/api/v1/resumes", headers={"Authorization": f"Bearer {token}"}, files=files
    )
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["error"]["message"]
