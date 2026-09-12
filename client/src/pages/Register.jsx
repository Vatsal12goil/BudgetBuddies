import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api";
import "../styles.css";

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "student",
  });

  const [toast, setToast] = useState(null);

  const showToast = (type, title, msg) => {
    setToast({ type, title, msg });
    setTimeout(() => setToast(null), 3000);
  };

  const register = async () => {
    if (!form.name || !form.email || !form.password) {
      showToast("error", "Missing Fields", "Please fill all fields");
      return;
    }

    try {
      await api.post("/register", form);

      showToast(
        "success",
        "Registration Successful",
        "Your account has been created"
      );

      setTimeout(() => navigate("/"), 1200);
    } catch (err) {
      showToast(
        "error",
        "Registration Failed",
        err.response?.data?.detail || "Something went wrong"
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
          <p className="subtitle">Create your account</p>

          <input
            className="input"
            type="text"
            placeholder="Full Name"
            value={form.name}
            onChange={(e) =>
              setForm({ ...form, name: e.target.value })
            }
          />

          <input
            className="input"
            type="email"
            placeholder="Email Address"
            value={form.email}
            onChange={(e) =>
              setForm({ ...form, email: e.target.value })
            }
          />

          <input
            className="input"
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) =>
              setForm({ ...form, password: e.target.value })
            }
          />

          <button className="btn" onClick={register}>
            Create Account
          </button>

          <p className="link">
            Already have an account? <Link to="/">Sign In</Link>
          </p>
        </div>
      </div>
    </>
  );
}