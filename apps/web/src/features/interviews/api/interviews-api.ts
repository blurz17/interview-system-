import { apiClient } from "../../../lib/api-client";
import { InterviewCreatePayload, InterviewSession, InterviewTurn } from "../types";

export const createInterviewSession = async (
  payload: InterviewCreatePayload
): Promise<InterviewSession> => {
  return apiClient.post<InterviewSession>("/api/v1/interviews", payload);
};

export const getInterviewSession = async (
  sessionId: string
): Promise<InterviewSession> => {
  return apiClient.get<InterviewSession>(`/api/v1/interviews/${sessionId}`);
};

export const startInterviewSession = async (
  sessionId: string
): Promise<InterviewTurn> => {
  return apiClient.post<InterviewTurn>(`/api/v1/interviews/${sessionId}/start`);
};

export const submitInterviewTurn = async (
  sessionId: string,
  content: string,
  inputMode: "text" | "voice" = "text"
): Promise<InterviewTurn> => {
  return apiClient.post<InterviewTurn>(`/api/v1/interviews/${sessionId}/turns`, {
    content,
    input_mode: inputMode,
  });
};

export const completeInterviewSession = async (
  sessionId: string
): Promise<InterviewSession> => {
  return apiClient.post<InterviewSession>(`/api/v1/interviews/${sessionId}/complete`);
};

export const abandonInterviewSession = async (
  sessionId: string
): Promise<InterviewSession> => {
  return apiClient.post<InterviewSession>(`/api/v1/interviews/${sessionId}/abandon`);
};

export const listInterviewSessions = async (): Promise<InterviewSession[]> => {
  return apiClient.get<InterviewSession[]>("/api/v1/interviews");
};
