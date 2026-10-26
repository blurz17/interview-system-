/**
 * Standard API Client following Bulletproof React conventions.
 * Encapsulates fetch with base URL, authorization headers, and error handling.
 */

export interface ApiErrorPayload {
  code: string;
  message: string;
  request_id?: string;
}

export class ApiError extends Error {
  public code: string;
  public status: number;
  public requestId?: string;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message || `API error with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.code = payload.code || "UNKNOWN_ERROR";
    this.requestId = payload.request_id;
  }
}

const AUTH_TOKEN_KEY = "careerpilot_access_token";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export const tokenStorage = {
  getToken: (): string | null => localStorage.getItem(AUTH_TOKEN_KEY),
  setToken: (token: string): void => localStorage.setItem(AUTH_TOKEN_KEY, token),
  clearToken: (): void => localStorage.removeItem(AUTH_TOKEN_KEY),
};

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const token = tokenStorage.getToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const targetUrl = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;

  const response = await fetch(targetUrl, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorPayload: ApiErrorPayload = {
      code: "HTTP_ERROR",
      message: response.statusText || "Request failed",
    };
    try {
      const data = await response.json();
      if (data?.error) {
        errorPayload = data.error;
      }
    } catch {
      // Body was not JSON
    }
    throw new ApiError(response.status, errorPayload);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestInit): Promise<T> =>
    request<T>(endpoint, { method: "GET", ...options }),

  post: <T>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> =>
    request<T>(endpoint, {
      method: "POST",
      body: data instanceof FormData ? data : JSON.stringify(data),
      ...options,
    }),

  put: <T>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> =>
    request<T>(endpoint, {
      method: "PUT",
      body: data instanceof FormData ? data : JSON.stringify(data),
      ...options,
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: RequestInit): Promise<T> =>
    request<T>(endpoint, {
      method: "PATCH",
      body: data instanceof FormData ? data : JSON.stringify(data),
      ...options,
    }),

  delete: <T>(endpoint: string, options?: RequestInit): Promise<T> =>
    request<T>(endpoint, { method: "DELETE", ...options }),
};
