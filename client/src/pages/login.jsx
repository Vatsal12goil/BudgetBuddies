import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api";
import "../styles.css";

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [toast, setToast] = useState(null);

  const showToast = (type, title, msg) => {
    setToast({ type, title, msg });
    setTimeout(() => setToast(null), 3000);
  };

  const login = async () => {
    if (!email || !password) {
      showToast("error", "Missing Fields", "Enter email and password");
      return;
    }

    try {
      const res = await api.post("/login", {
        email,
        password,
      });

      localStorage.setItem("token", res.data.access_token);

      showToast("success", "Welcome Back", "Login Successful");

      setTimeout(() => navigate("/dashboard"), 900);

    } catch (err) {
      showToast(
        "error",
        "Login Failed",
        err.response?.data?.detail || "Invalid Credentials"
      );
    }
  };

  return (
    <>
      {toast && (
        <div className={`toast ${toast.type}`}>
          <div className="toast-icon">
            {toast.type === "success" ? "✅" : "❌"}
          </div>

          <div>
            <div className="toast-title">{toast.title}</div>
            <div className="toast-msg">{toast.msg}</div>
          </div>
        </div>
      )}

      <div className="auth-page">
        <div className="card">
          <h1 className="logo">💰 BudgetBuddy</h1>
          <p className="subtitle">Welcome back</p>

          <input
            className="input"
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <input
            className="input"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button className="btn" onClick={login}>
            Sign In
          </button>

          <p className="link">
            New user? <Link to="/register">Create Account</Link>
          </p>
        </div>
      </div>
    </>
  );
}