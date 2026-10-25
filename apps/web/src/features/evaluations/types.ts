export type EvaluationStatus = "pending" | "completed" | "failed";

export interface SkillEvidencePublic {
  id: string;
  skill_id: string;
  skill_name: string;
  skill_slug: string;
  score: number;
  evidence_type: string;
  evidence_reference?: string | null;
  explanation: string;
  confidence: number;
  created_at: string;
}

export interface EvaluationReportPublic {
  id: string;
  session_id: string;
  overall_score: number;
  rubric_version: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  evaluation_status: EvaluationStatus;
  skill_evidences: SkillEvidencePublic[];
  created_at: string;
}
