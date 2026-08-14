import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { useAuthStore } from "@/stores/auth-store";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// A separate, un-intercepted instance for the refresh call itself — if this
// used `apiClient`, a failing refresh would recurse into the same 401
// handler that triggered it.
const refreshClient = axios.create({ baseURL: API_BASE_URL });

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh tokens are single-use (server-side rotation) — if two requests
// 401 at once, only one refresh call may actually happen, or the second one
// invalidates the token the first is still waiting on. This dedupes
// concurrent refreshes into one in-flight promise every caller awaits.
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const currentRefreshToken = useAuthStore.getState().refreshToken;
  if (!currentRefreshToken) return null;

  try {
    const { data } = await refreshClient.post("/auth/refresh", {
      refresh_token: currentRefreshToken,
    });
    useAuthStore.getState().setTokens({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    });
    return data.access_token as string;
  } catch {
    useAuthStore.getState().clearAuth();
    return null;
  }
}

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableConfig | undefined;
    const isAuthEndpoint = originalRequest?.url?.includes("/auth/");

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthEndpoint
    ) {
      originalRequest._retry = true;

      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }

      const newAccessToken = await refreshPromise;

      if (newAccessToken) {
        originalRequest.headers.set("Authorization", `Bearer ${newAccessToken}`);
        return apiClient(originalRequest);
      }

      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);
