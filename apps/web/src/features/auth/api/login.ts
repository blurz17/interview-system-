import { apiClient, tokenStorage } from "../../../lib/api-client";
import { AuthResponse } from "../types";

export interface LoginCredentials {
  email: string;
  password: string;
}

export const REFRESH_TOKEN_KEY = "careerpilot_refresh_token";

export const loginWithCredentials = async (
  credentials: LoginCredentials
): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>("/api/v1/auth/login", credentials);
  tokenStorage.setToken(response.tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, response.tokens.refresh_token);
  return response;
};
