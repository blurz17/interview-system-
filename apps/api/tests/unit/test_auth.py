import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    payload = {
        "email": "candidate1@university.edu",
        "password": "SecurePassword123!",
        "full_name": "Jane Student",
        "target_role": "Backend Engineer",
        "experience_level": "intermediate",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert "tokens" in data
    assert data["user"]["email"] == "candidate1@university.edu"
    assert data["user"]["profile"]["full_name"] == "Jane Student"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]
    assert data["tokens"]["token_type"] == "bearer"
    assert "access_token" in data["tokens"]
    assert "refresh_token" in data["tokens"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "email": "duplicate@university.edu",
        "password": "SecurePassword123!",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Same email in different casing
    payload["email"] = "DUPLICATE@university.edu"
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login_test@university.edu", "password": "Password123!"},
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login_test@university.edu", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "login_test@university.edu"
    assert "access_token" in data["tokens"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bad_login@university.edu", "password": "CorrectPassword123!"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "bad_login@university.edu", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_current_user_me(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "me_test@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]

    # Call /me with token
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me_test@university.edu"

    # Call /me without token
    unauth = await client.get("/api/v1/auth/me")
    assert unauth.status_code == 401


@pytest.mark.asyncio
async def test_patch_profile(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "patch_test@university.edu", "password": "Password123!"},
    )
    token = reg.json()["tokens"]["access_token"]

    response = await client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Updated Name",
            "target_role": "Full Stack Engineer",
            "experience_level": "advanced",
        },
    )
    assert response.status_code == 200
    profile = response.json()["profile"]
    assert profile["full_name"] == "Updated Name"
    assert profile["target_role"] == "Full Stack Engineer"
    assert profile["experience_level"] == "advanced"


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_revocation(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh_test@university.edu", "password": "Password123!"},
    )
    tokens1 = reg.json()["tokens"]
    rt1 = tokens1["refresh_token"]

    # Rotate token
    ref_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rt1},
    )
    assert ref_res.status_code == 200
    tokens2 = ref_res.json()["tokens"]
    rt2 = tokens2["refresh_token"]
    assert rt2 != rt1

    # Old token rt1 is now revoked! Attempting to reuse it must trigger family revocation
    reused = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rt1},
    )
    assert reused.status_code == 401
    assert "reuse detected" in reused.json()["error"]["message"]

    # And now even rt2 should have been revoked by the family revocation policy
    reused_child = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rt2},
    )
    assert reused_child.status_code == 401
