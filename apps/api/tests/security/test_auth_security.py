from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_cross_user_isolation(client: AsyncClient):
    # Register User A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "user_a@university.edu", "password": "Password123!", "full_name": "User A"},
    )
    user_a_id = res_a.json()["user"]["id"]

    # Register User B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "user_b@university.edu", "password": "Password123!", "full_name": "User B"},
    )
    token_b = res_b.json()["tokens"]["access_token"]

    # User B requests /me -> gets User B, not User A
    me_b = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert me_b.status_code == 200
    assert me_b.json()["id"] != user_a_id
    assert me_b.json()["email"] == "user_b@university.edu"
    assert me_b.json()["profile"]["full_name"] == "User B"


@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient):
    # Create an already-expired token (-5 minutes)
    expired_token = create_access_token(
        subject="11111111-2222-3333-4444-555555555555",
        expires_delta=timedelta(minutes=-5),
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_tampered_token_rejected(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "tamper@university.edu", "password": "Password123!"},
    )
    valid_token = reg.json()["tokens"]["access_token"]
    tampered_token = valid_token[:-4] + "fake"

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401
