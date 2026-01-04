import {useState} from "react";
import {useNavigate} from "react-router-dom";
import {login} from "../api/auth";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const nav = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await login(username, password);
    nav("/dashboard");
  }

  return (
    <form onSubmit={handleSubmit}>
      <input placeholder="username" onChange={(e) => setUsername(e.target.value)} />
      <input placeholder="password" type="password" onChange={(e) => setPassword(e.target.value)} />
      <button type="submit">Login</button>
    </form>
  );
}