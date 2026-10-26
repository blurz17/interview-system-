export interface HardRequirementResult {
  id: string;
  requirement: string;
  status: "Passed" | "Partial" | "Missing";
  weight: string;
  cv_evidence: string;
  matches: string[];
  similarity_index?: number;
}

export interface BonusSkillResult {
  skill: string;
  matched: boolean;
  notes: string;
}

export interface JobMeta {
  title: string;
  company: string;
  location: string;
  url?: string;
}

export interface JobHunterAnalysisResult {
  overall_match_score: number;
  verdict: string;
  job_meta: JobMeta;
  candidate_location: string;
  location_eligible: boolean;
  location_notes: string;
  timezone_eligible: boolean;
  timezone_notes: string;
  hard_requirements_analysis: HardRequirementResult[];
  bonus_points_analysis: BonusSkillResult[];
  key_strengths: string[];
  critical_gaps: string[];
  tailored_cv_bullets_to_add: string[];
  recruiter_outreach_message: string;
  engine_used: string;
}

export interface FetchJobResponse {
  source: string;
  title: string;
  company: string;
  location: string;
  description: string;
  url?: string;
}
