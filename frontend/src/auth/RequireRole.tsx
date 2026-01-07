import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { AccountType } from "../api/me";

function homeFor(role: AccountType) {
  return role === "AP" ? "/applicant/jobs" : "/employer/jobs";
}

export default function RequireRole({ role }: { role: AccountType }) {
  const { accountType, loading } = useAuth();

  if (loading) return null; // or a loading UI

  if (!accountType) {
    return <Navigate to="/login" replace />;
  }

  if (accountType !== role) {
    return <Navigate to={homeFor(accountType)} replace />;
  }

  return <Outlet />;
}