import { apiClient } from "../../../lib/api-client";
import { CodingSubmissionCreate, CodingSubmissionPublic, TestResultPublic } from "../types";

export const submitCode = async (
  sessionId: string,
  payload: CodingSubmissionCreate
): Promise<CodingSubmissionPublic> => {
  return apiClient.post<CodingSubmissionPublic>(
    `/api/v1/interviews/${sessionId}/submissions`,
    payload
  );
};

export const getSubmission = async (
  submissionId: string
): Promise<CodingSubmissionPublic> => {
  return apiClient.get<CodingSubmissionPublic>(`/api/v1/submissions/${submissionId}`);
};

export const getSubmissionResults = async (
  submissionId: string
): Promise<TestResultPublic[]> => {
  return apiClient.get<TestResultPublic[]>(`/api/v1/submissions/${submissionId}/results`);
};
