from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    text: str
    provider: str
    confidence: float
    duration_seconds: float | None = None


class SpeechSynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice: str = "default"


class SpeechCapabilitiesResponse(BaseModel):
    stt_provider: str
    tts_provider: str
    web_speech_supported: bool
    max_audio_size_bytes: int
