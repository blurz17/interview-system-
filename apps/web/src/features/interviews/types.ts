export type InterviewType = "technical" | "coding" | "system_design";
export type InteractionMode = "text" | "voice";
export type InterviewStatus = "created" | "in_progress" | "completed" | "abandoned" | "failed";
export type TurnSpeaker = "assistant" | "candidate";

export interface InterviewTurn {
  id: string;
  sequence_number: number;
  speaker: TurnSpeaker;
  question_id?: string;
  content: string;
  input_mode: InteractionMode;
  turn_metadata?: {
    question_number?: number;
    is_final?: boolean;
    [key: string]: unknown;
  };
  created_at: string;
}

export interface InterviewSession {
  id: string;
  target_role: string;
  interview_type: InterviewType;
  interaction_mode: InteractionMode;
  difficulty: "beginner" | "intermediate" | "advanced";
  status: InterviewStatus;
  resume_id?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  turns?: InterviewTurn[];
}

export interface InterviewCreatePayload {
  target_role: string;
  interview_type: InterviewType;
  interaction_mode: InteractionMode;
  difficulty: "beginner" | "intermediate" | "advanced";
  resume_id?: string;
}
