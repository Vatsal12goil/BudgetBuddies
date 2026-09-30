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
      // Register user in backend
      await api.post("/register", form);

      // Save account locally for Remember Me
      const accounts = JSON.parse(
        localStorage.getItem("savedAccounts") || "[]"
      );

      const account = {
        name: form.name,
        email: form.email,
        password: form.password,
      };

      const index = accounts.findIndex(
        (a) => a.email === form.email
      );

      if (index >= 0) {
        accounts[index] = account;
      } else {
        accounts.push(account);
      }

      localStorage.setItem(
        "savedAccounts",
        JSON.stringify(accounts)
      );

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

          <form
            autoComplete="on"
            onSubmit={(e) => {
              e.preventDefault();
              register();
            }}
          >
            <input
              className="input"
              type="text"
              name="name"
              autoComplete="name"
              placeholder="Full Name"
              value={form.name}
              onChange={(e) =>
                setForm({ ...form, name: e.target.value })
              }
            />

            <input
              className="input"
              type="email"
              name="email"
              autoComplete="username"
              placeholder="Email Address"
              value={form.email}
              onChange={(e) =>
                setForm({ ...form, email: e.target.value })
              }
            />

            <input
              className="input"
              type="password"
              name="password"
              autoComplete="new-password"
              placeholder="Password"
              value={form.password}
              onChange={(e) =>
                setForm({
                  ...form,
                  password: e.target.value,
                })
              }
            />

            <button type="submit" className="btn">
              Create Account
            </button>
          </form>

          <p className="link">
            Already have an account?{" "}
            <Link to="/">Sign In</Link>
          </p>
        </div>
      </div>
    </>
  );
}