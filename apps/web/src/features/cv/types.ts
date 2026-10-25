export interface Skill {
  id: string;
  slug: string;
  name: string;
  description?: string;
  category: string;
  difficulty_level: "beginner" | "intermediate" | "advanced";
  is_active: boolean;
  prerequisites: { id: string; slug: string; name: string }[];
}

export interface ResumeSkill {
  id: string;
  skill_id: string;
  skill_name: string;
  skill_slug: string;
  category: string;
  evidence_text?: string;
  extraction_confidence: number;
  source_section?: string;
}

export interface Resume {
  id: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  parsing_status: "pending" | "processing" | "completed" | "failed";
  extraction_status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  skills: ResumeSkill[];
}
