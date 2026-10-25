import { apiClient, tokenStorage } from "../../../lib/api-client";
import { User } from "../types";

export const getCurrentUser = async (): Promise<User | null> => {
  const token = tokenStorage.getToken();
  if (!token) return null;

  try {
    return await apiClient.get<User>("/api/v1/auth/me");
  } catch {
    tokenStorage.clearToken();
    return null;
  }
};
