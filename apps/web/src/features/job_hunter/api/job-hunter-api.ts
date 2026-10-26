import { apiClient } from "../../../lib/api-client";
import { FetchJobResponse, JobHunterAnalysisResult } from "../types";

export const fetchJobDetails = async (url: string): Promise<FetchJobResponse> => {
  return apiClient.post<FetchJobResponse>("/api/v1/job-hunter/fetch-job", { url });
};

export const analyzeJobFit = async (formData: FormData): Promise<JobHunterAnalysisResult> => {
  return apiClient.post<JobHunterAnalysisResult>("/api/v1/job-hunter/analyze", formData);
};
