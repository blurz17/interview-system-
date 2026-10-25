export interface TranscriptionResponse {
  text: string;
  provider: string;
  confidence: number;
  duration_seconds?: number | null;
}

export interface SpeechCapabilitiesResponse {
  stt_provider: string;
  tts_provider: string;
  web_speech_supported: boolean;
  max_audio_size_bytes: number;
}
