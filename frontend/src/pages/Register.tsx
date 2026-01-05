import {useState} from "react";
import {useNavigate} from "react-router-dom";
import {register} from "../api/auth";

export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const nav = useNavigate();

    async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await register(username, password, email);
    nav("/login");
  }
    return (
      <div id="register-container">
        <form onSubmit={handleSubmit}>
          <input placeholder="username" onChange={(e) => setUsername(e.target.value)} />
          <input placeholder="email" onChange={(e) => setEmail(e.target.value)} />
          <input placeholder="password" type="password" onChange={(e) => setPassword(e.target.value)} />
            <button type="submit">Register</button>
            <br />
            <button type="button" onClick={() => nav("/login")}>Already have an account?</button>
        </form>
      </div>
    );
}