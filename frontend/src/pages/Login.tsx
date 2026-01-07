import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const nav = useNavigate();
  const { refreshMe } = useAuth();

async function handleSubmit(e: React.FormEvent) {
  e.preventDefault();

  await login(username, password);
  const me = await refreshMe();   // type = Me

  nav(
    me.account_type === "EM" ? "/employer/jobs" : "/applicant/jobs",
    { replace: true }
  );
}


  return (
    <div id="login-container">
      <form onSubmit={handleSubmit}>
        <input placeholder="username" onChange={(e) => setUsername(e.target.value)} />
        <input placeholder="password" type="password" onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">Login</button>
        <br />
        <button type="button" onClick={() => nav("/register")}>Register</button>
      </form>
    </div>
  );
}
