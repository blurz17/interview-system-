import { apiClient, tokenStorage } from "../../../lib/api-client";
import { AuthResponse } from "../types";
import { REFRESH_TOKEN_KEY } from "./login";

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
  target_role?: string;
  experience_level?: "beginner" | "intermediate" | "advanced";
}

export const registerCandidate = async (
  payload: RegisterPayload
): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>("/api/v1/auth/register", payload);
  tokenStorage.setToken(response.tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, response.tokens.refresh_token);
  return response;
};
