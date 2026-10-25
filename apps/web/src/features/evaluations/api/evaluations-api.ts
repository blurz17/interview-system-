import { apiClient } from "../../../lib/api-client";
import { EvaluationReportPublic } from "../types";

export const getEvaluationReport = async (
  sessionId: string
): Promise<EvaluationReportPublic> => {
  return apiClient.get<EvaluationReportPublic>(`/api/v1/interviews/${sessionId}/report`);
};

export const evaluateSession = async (
  sessionId: string
): Promise<EvaluationReportPublic> => {
  return apiClient.post<EvaluationReportPublic>(`/api/v1/interviews/${sessionId}/evaluate`);
};
