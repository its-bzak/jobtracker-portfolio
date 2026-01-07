import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export default function RoleHomeRedirect() {
  const { accountType, loading } = useAuth();

  if (loading) return null;

  if (accountType === "EM") return <Navigate to="/employer/jobs" replace />;
  if (accountType === "AP") return <Navigate to="/app/jobs" replace />;

  return <Navigate to="/login" replace />;
}
