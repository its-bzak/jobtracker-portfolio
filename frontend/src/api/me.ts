import { api } from "./client";

export type AccountType = "AP" | "EM";

export type Me = {
  id: number;
  username: string;
  email: string;
  account_type: AccountType;
};

export async function getMe(): Promise<Me> {
  const response = await api.get<Me>("/api/auth/me/");
  return response.data;
}
