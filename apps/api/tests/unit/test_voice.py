import io

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_voice_capabilities(client: AsyncClient):
    resp = await client.get("/api/v1/voice/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert "stt_provider" in data
    assert "tts_provider" in data
    assert data["web_speech_supported"] is True
    assert data["max_audio_size_bytes"] == 10 * 1024 * 1024


@pytest.mark.asyncio
async def test_transcribe_audio_success(client: AsyncClient):
    # Register user
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "voice_candidate@example.edu", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['tokens']['access_token']}"}

    # Create dummy wav bytes
    dummy_wav = io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00data\x00\x00\x00\x00")

    resp = await client.post(
        "/api/v1/voice/transcriptions",
        headers=headers,
        files={"file": ("recording.wav", dummy_wav, "audio/wav")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "text" in data
    assert len(data["text"]) > 0
    assert data["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_transcribe_unsupported_audio_rejected(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "voice_reject@example.edu", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['tokens']['access_token']}"}

    dummy_file = io.BytesIO(b"%PDF-1.4 dummy content")
    resp = await client.post(
        "/api/v1/voice/transcriptions",
        headers=headers,
        files={"file": ("doc.pdf", dummy_file, "application/pdf")},
    )
    assert resp.status_code == 400
    assert "Unsupported audio format" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_generate_speech_directive(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": "voice_tts@example.edu", "password": "Password123!"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['tokens']['access_token']}"}

    resp = await client.post(
        "/api/v1/voice/speech",
        headers=headers,
        json={"text": "Can you explain optimistic concurrency control?", "voice": "default"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "web_speech_api"
    assert data["text"] == "Can you explain optimistic concurrency control?"
