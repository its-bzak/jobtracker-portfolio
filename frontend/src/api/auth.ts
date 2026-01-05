import { api } from "./client";
import { tokenStorage } from "../auth/tokenStorage";

export async function login(username: string, password: string) {
  const resp = await api.post("/api/auth/login/", {
    username,
    password,
  });

  const { access, refresh } = resp.data;
  if (!access || !refresh) {
    throw new Error("Missing access or refresh token");
  }

  tokenStorage.setAccess(access);
  tokenStorage.setRefresh(refresh);
}

export async function logout() {
  const refresh = tokenStorage.getRefresh();

  try {
    if (refresh) {
      await api.post("/api/auth/logout/", { refresh });
    }
  } finally {
    tokenStorage.clear();
  }
}

export function isLoggedIn(): boolean {
  return !!tokenStorage.getAccess();
}

export async function register(username: string, password: string, email: string) {
  await api.post("/api/auth/register/", {
    username,
    password,
    email,
  });
}