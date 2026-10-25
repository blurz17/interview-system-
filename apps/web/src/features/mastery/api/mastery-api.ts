import { apiClient } from "../../../lib/api-client";
import {
  TrainingAssignmentPublic,
  TrainingAttemptCreate,
  TrainingAttemptPublic,
  TrainingSolveResponse,
  UserSkillMasteryPublic,
} from "../types";

export const getSkillMastery = async (): Promise<UserSkillMasteryPublic[]> => {
  return apiClient.get<UserSkillMasteryPublic[]>("/api/v1/skills/mastery");
};

export const getTrainingAssignments = async (): Promise<TrainingAssignmentPublic[]> => {
  return apiClient.get<TrainingAssignmentPublic[]>("/api/v1/training/assignments");
};

export const generateTrainingAssignments = async (): Promise<TrainingAssignmentPublic[]> => {
  return apiClient.post<TrainingAssignmentPublic[]>("/api/v1/training/assignments/generate");
};

export const submitTrainingAttempt = async (
  assignmentId: string,
  payload: TrainingAttemptCreate
): Promise<TrainingAttemptPublic> => {
  return apiClient.post<TrainingAttemptPublic>(
    `/api/v1/training/assignments/${assignmentId}/attempts`,
    payload
  );
};

export const solveTrainingAssignment = async (
  assignmentId: string,
  candidateAnswer: string
): Promise<TrainingSolveResponse> => {
  return apiClient.post<TrainingSolveResponse>(
    `/api/v1/training/assignments/${assignmentId}/solve`,
    { candidate_answer: candidateAnswer }
  );
};
