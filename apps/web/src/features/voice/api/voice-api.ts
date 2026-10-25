import { apiClient } from "../../../lib/api-client";
import { SpeechCapabilitiesResponse, TranscriptionResponse } from "../types";

export const getVoiceCapabilities = async (): Promise<SpeechCapabilitiesResponse> => {
  return apiClient.get<SpeechCapabilitiesResponse>("/api/v1/voice/capabilities");
};

export const transcribeAudio = async (audioBlob: Blob): Promise<TranscriptionResponse> => {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.wav");
  return apiClient.post<TranscriptionResponse>("/api/v1/voice/transcriptions", formData);
};
