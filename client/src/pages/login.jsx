import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api";
import "../styles.css";

export default function Login() {
  const navigate = useNavigate();

  const [savedAccounts, setSavedAccounts] = useState(() => {
  try {
    return JSON.parse(localStorage.getItem("savedAccounts") || "[]");
  } catch {
    return [];
  }
});

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
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

      if (remember) {
        const accounts = JSON.parse(
          localStorage.getItem("savedAccounts") || "[]"
        );

        const account = {
          name: email.split("@")[0],
          email,
          password,
        };

        const index = accounts.findIndex((a) => a.email === email);

        if (index >= 0) {
          accounts[index] = account;
        } else {
          accounts.push(account);
        }

        localStorage.setItem(
          "savedAccounts",
          JSON.stringify(accounts)
        );
        setSavedAccounts([...accounts]);
      }

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

  const deleteAccount = (mail) => {
    const updated = savedAccounts.filter((a) => a.email !== mail);
    localStorage.setItem(
      "savedAccounts",
      JSON.stringify(updated)
    );
    setSavedAccounts(updated);

    if (email === mail) {
      setEmail("");
      setPassword("");
      setRemember(false);
    }
  };
  // Clear login form
  const clearForm = () => {
    setEmail("");
    setPassword("");
    setRemember(false);
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
          {savedAccounts.length > 0 && (
            <button
              type="button"
              onClick={clearForm}
              style={{
                width: "100%",
                background: "#F3F4F6",
                border: "1px solid #E5E7EB",
                borderRadius: 10,
                padding: "10px",
                margin: "12px 0 16px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Use Another Account
            </button>
          )}
          {savedAccounts.length > 0 && (
            <div style={{ marginBottom: 18 }}>
              <p
                style={{
                  fontSize: 13,
                  color: "#666",
                  marginBottom: 10,
                }}
              >
                Saved Accounts
              </p>

              {savedAccounts.map((acc) => (
                <div
                  key={acc.email}
                  onClick={() => {
                    setEmail(acc.email);
                    setPassword(acc.password);
                    setRemember(true);
                  }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "10px 12px",
                    border: "1px solid #ECECEC",
                    borderRadius: 10,
                    marginBottom: 8,
                    cursor: "pointer",
                    background: "#FAFAFA",
                  }}
                >
                  <div
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: "50%",
                      background: "#5B3DF5",
                      color: "#fff",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: 700,
                    }}
                  >
                    {acc.name.charAt(0).toUpperCase()}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: 14,
                      }}
                    >
                      {acc.name}
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        color: "#777",
                      }}
                    >
                      {acc.email}
                    </div>
                  </div>

                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteAccount(acc.email);
                    }}
                    style={{
                      color: "#DC2626",
                      fontWeight: 700,
                      cursor: "pointer",
                      padding: "0 6px",
                    }}
                  >
                    ✕
                  </span>
                </div>
              ))}
            </div>
          )}

          <form
            autoComplete="on"
            onSubmit={(e) => {
              e.preventDefault();
              login();
            }}
          >
            <input
              className="input"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <input
              className="input"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                margin: "12px 0 18px",
              }}
            >
              <input
                type="checkbox"
                id="remember"
                checked={remember}
                onChange={(e) =>
                  setRemember(e.target.checked)
                }
              />

              <label
                htmlFor="remember"
                style={{
                  fontSize: 14,
                  color: "#555",
                  cursor: "pointer",
                }}
              >
                Remember Me
              </label>
            </div>

            <button type="submit" className="btn">
              Sign In
            </button>
          </form>

          <p className="link">
            New user? <Link to="/register">Create Account</Link>
          </p>
        </div>
      </div>
    </>
  );
}