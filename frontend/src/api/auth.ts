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

export function logout() {
  tokenStorage.clear();
}

export function isLoggedIn(): boolean {
  return !!tokenStorage.getAccess();
}