import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { logout } from "../api/auth";

export default function Logout() {
  const navigate = useNavigate();

  useEffect(() => {
    logout().finally(() => {
      navigate("/login", { replace: true });
    });
  }, [navigate]);

  return <p>Logging out</p>;
}
