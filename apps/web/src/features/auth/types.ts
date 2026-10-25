export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  profile?: CandidateProfile;
}

export interface CandidateProfile {
  id: string;
  user_id: string;
  full_name?: string | null;
  target_role?: string | null;
  experience_level: "beginner" | "intermediate" | "advanced";
  preferred_language: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}
