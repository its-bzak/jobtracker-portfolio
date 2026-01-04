import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";
import { tokenStorage } from "../auth/tokenStorage";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = tokenStorage.getRefresh();
  if (!refresh) throw new Error("No refresh token");

  const resp = await axios.post(
    `${API_BASE_URL}/api/auth/refresh/`,
    { refresh },
    { headers: { "Content-Type": "application/json" } }
  );

  const newAccess = resp.data?.access;
  if (!newAccess) throw new Error("No access token in refresh response");

  tokenStorage.setAccess(newAccess);
  return newAccess;
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const originalRequest: any = error.config;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      try {
        if (!isRefreshing) {
          isRefreshing = true;
          refreshPromise = refreshAccessToken().finally(() => {
            isRefreshing = false;
            refreshPromise = null;
          });
        }

        const newToken = await refreshPromise!;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch {
        tokenStorage.clear();
      }
    }

    return Promise.reject(error);
  }
);
