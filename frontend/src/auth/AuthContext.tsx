import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { getMe, type Me, type AccountType } from "../api/me";
import { tokenStorage } from "./tokenStorage";

type AuthState = {
  me: Me | null;
  accountType: AccountType | null;
  loading: boolean;
  refreshMe: () => Promise<Me>;
  clearMe: () => void;
  hasNewApplicationDraft: boolean;
  markNewApplicationDraft: (v: boolean) => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [accountType, setAccountType] = useState<AccountType | null>(null);
  const [loading, setLoading] = useState(true);
  const [hasNewApplicationDraft, setHasNewApplicationDraft] = useState(false);

  async function refreshMe(): Promise<Me> {
    const data = await getMe();
    setMe(data);
    setAccountType(data.account_type);
    return data;
  }

  function clearMe() {
    setMe(null);
    setAccountType(null);
  }

  function markNewApplicationDraft(v: boolean) {
    setHasNewApplicationDraft(v);
  }

  useEffect(() => {
    // If theres no token
    const access = tokenStorage.getAccess?.();
    if (!access) {
      setLoading(false);
      return;
    }

    refreshMe()
      .catch(() => {
        // invalid or expired token
        clearMe();
        tokenStorage.clear?.();
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({ me, accountType, loading, refreshMe, clearMe, hasNewApplicationDraft, markNewApplicationDraft }),
    [me, accountType, loading, hasNewApplicationDraft]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
