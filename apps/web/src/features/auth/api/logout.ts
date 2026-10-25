import { apiClient, tokenStorage } from "../../../lib/api-client";
import { REFRESH_TOKEN_KEY } from "./login";

export const logoutCandidate = async (): Promise<void> => {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
  if (refreshToken) {
    try {
      await apiClient.post("/api/v1/auth/logout", { refresh_token: refreshToken });
    } catch {
      // Ignore network errors on logout
    }
  }
  tokenStorage.clearToken();
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};
