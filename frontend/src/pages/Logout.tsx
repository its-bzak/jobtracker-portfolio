import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { logout } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export default function Logout() {
  const navigate = useNavigate();
  const { clearMe } = useAuth();

  useEffect(() => {
    logout().finally(() => {
      clearMe(); // ✅ clears role/user state immediately
      navigate("/login", { replace: true });
    });
  }, [navigate, clearMe]);

  return <p>Logging out</p>;
}
