import { apiClient } from "../../../lib/api-client";
import { Resume, Skill } from "../types";

export const uploadResumeFile = async (file: File): Promise<Resume> => {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.post<Resume>("/api/v1/resumes", formData);
};

export const getResumes = async (): Promise<Resume[]> => {
  return apiClient.get<Resume[]>("/api/v1/resumes");
};

export const getAvailableSkills = async (): Promise<Skill[]> => {
  return apiClient.get<Skill[]>("/api/v1/skills");
};

export const updateResumeSkills = async (
  resumeId: string,
  skillSlugs: string[]
): Promise<Resume> => {
  return apiClient.patch<Resume>(`/api/v1/resumes/${resumeId}/skills`, {
    skill_slugs: skillSlugs,
  });
};

export const deleteResumeFile = async (resumeId: string): Promise<void> => {
  return apiClient.delete<void>(`/api/v1/resumes/${resumeId}`);
};
