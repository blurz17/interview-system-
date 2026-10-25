from fastapi import APIRouter, File, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.deps import CurrentUser
from app.core.config import settings
from app.core.errors import BadRequestError
from app.integrations.speech.provider import speech_provider
from app.schemas.voice import (
    SpeechCapabilitiesResponse,
    SpeechSynthesisRequest,
    TranscriptionResponse,
)

router = APIRouter(prefix="/voice", tags=["Voice & Speech"])

MAX_AUDIO_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.get(
    "/capabilities",
    response_model=SpeechCapabilitiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Report supported voice and speech capabilities",
)
async def get_voice_capabilities() -> SpeechCapabilitiesResponse:
    return SpeechCapabilitiesResponse(
        stt_provider=settings.SPEECH_PROVIDER,
        tts_provider=settings.TTS_PROVIDER,
        web_speech_supported=True,
        max_audio_size_bytes=MAX_AUDIO_SIZE_BYTES,
    )


@router.post(
    "/transcriptions",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Convert uploaded candidate audio to text without permanent audio storage",
)
async def transcribe_audio(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> TranscriptionResponse:
    content_type = file.content_type or "audio/wav"
    audio_bytes = await file.read()

    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise BadRequestError("Audio file exceeds maximum size limit of 10 MB.")

    result = await speech_provider.transcribe_audio(
        audio_bytes=audio_bytes,
        content_type=content_type,
    )

    return TranscriptionResponse(
        text=result.text,
        provider=result.provider,
        confidence=result.confidence,
        duration_seconds=result.duration_seconds,
    )


@router.post(
    "/speech",
    status_code=status.HTTP_200_OK,
    summary="Generate speech synthesis or return Web Speech API directives",
)
async def generate_speech(
    current_user: CurrentUser,
    payload: SpeechSynthesisRequest,
) -> JSONResponse:
    # Per Section 8.3 & Section 11.7:
    # Web Speech API in the client is primary for low-latency native browser synthesis.
    # Return synthesis directive with sanitized text.
    return JSONResponse(
        content={
            "mode": "web_speech_api",
            "text": payload.text,
            "voice": payload.voice,
            "rate": 1.0,
            "pitch": 1.0,
        }
    )
