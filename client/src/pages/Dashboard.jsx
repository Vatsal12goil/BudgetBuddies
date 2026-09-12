import { useEffect, useState } from "react";
import api from "../api";
import "../styles.css";

export default function Dashboard() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    api
      .get("/me", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      })
      .then((res) => setUser(res.data));
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    window.location.href = "/";
  };

  return (
    <div className="dashboard-page">
      {/* Top Navbar */}
      <div className="navbar">
        <div>
          <h2>💰 BudgetBuddy</h2>
          <p>Smart Expense Tracker</p>
        </div>

        <button className="logout-btn" onClick={logout}>
          Logout
        </button>
      </div>

      {/* Welcome Banner */}
      <div className="welcome-banner">
        <div>
          <h1>Hello, {user?.name} 👋</h1>
          <p>{user?.email}</p>
        </div>

        <div className="role-badge">{user?.role}</div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <span>💳 Total Balance</span>
          <h2>₹18,500</h2>
        </div>

        <div className="stat-card">
          <span>📅 Monthly Budget</span>
          <h2>₹10,000</h2>
        </div>

        <div className="stat-card">
          <span>💸 Expenses</span>
          <h2>₹2,450</h2>
        </div>

        <div className="stat-card">
          <span>💰 Savings</span>
          <h2>₹7,550</h2>
        </div>
      </div>

      {/* Transactions */}
      <div className="table-card">
        <div className="table-head">
          <h3>Recent Transactions</h3>
          <span>This Month</span>
        </div>

        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Category</th>
              <th>Amount</th>
            </tr>
          </thead>

          <tbody>
            <tr>
              <td>🍔 Food</td>
              <td>Dining</td>
              <td>₹250</td>
            </tr>

            <tr>
              <td>🚇 Travel</td>
              <td>Metro</td>
              <td>₹120</td>
            </tr>

            <tr>
              <td>🛍 Shopping</td>
              <td>Amazon</td>
              <td>₹980</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}