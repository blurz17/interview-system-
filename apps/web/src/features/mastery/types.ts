export type AssignmentStatus = "pending" | "in_progress" | "completed" | "abandoned";

export interface UserSkillMasteryPublic {
  id: string;
  user_id: string;
  skill_id: string;
  skill_name: string;
  skill_slug: string;
  category: string;
  mastery_score: number;
  confidence: number;
  evidence_count: number;
  last_assessed_at: string;
}

export interface TrainingAssignmentPublic {
  id: string;
  user_id: string;
  skill_id: string;
  skill_name: string;
  title: string;
  description: string;
  exercise_type: string;
  difficulty: "beginner" | "intermediate" | "advanced";
  status: AssignmentStatus;
  created_at: string;
  completed_at?: string | null;
}

export interface TrainingAttemptCreate {
  score: number;
  result_summary: string;
}

export interface TrainingAttemptPublic {
  id: string;
  assignment_id: string;
  user_id: string;
  score: number;
  result_summary: string;
  completed_at: string;
}
