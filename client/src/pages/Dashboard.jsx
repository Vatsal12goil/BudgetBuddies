import { useEffect, useState } from "react";
import api from "../api";
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function Dashboard() {
  const token = localStorage.getItem("token");

  const [user, setUser] = useState({});
  const [activeTab, setActiveTab] = useState("Dashboard");

  const [dashboard, setDashboard] = useState({
    total_income: 0,
    total_expense: 0,
    remaining_amount: 0,
    recent_activity: [],
  });

  const [monthlyBudget, setMonthlyBudget] = useState(0);
  const [budgets, setBudgets] = useState([]);
  const [editingBudget, setEditingBudget] = useState(null);

  const [expenseForm, setExpenseForm] = useState({
    title: "",
    amount: "",
    category: "Food",
  });
  const [expenses, setExpenses] = useState([]);
  const [editingExpense, setEditingExpense] = useState(null);
  const [incomes, setIncomes] = useState([]);

  const [incomeForm, setIncomeForm] = useState({
    amount: "",
    source: "Pocket Money",
    description: "",
  });
  const [editingIncome, setEditingIncome] = useState(null);

  const currentMonth = new Date().toISOString().slice(0, 7);
  const [selectedMonth, setSelectedMonth] = useState(currentMonth);

  const [budgetForm, setBudgetForm] = useState({
    category: "Food",
    amount: "",
    month: currentMonth, // YYYY-MM
  });
  const [goals, setGoals] = useState([]);
  const [editingGoal, setEditingGoal] = useState(null);

  const [goalForm, setGoalForm] = useState({
    goal_name: "",
    target_amount: "",
    current_saved: "",
  });
  const [notifications, setNotifications] = useState([]);
  const [dashboardError, setDashboardError] = useState("");
  const [analytics, setAnalytics] = useState(null);
  const [loadingAnalytics, setLoadingAnalytics] = useState(false);
  const [analyticsError, setAnalyticsError] = useState("");
  const [profileForm, setProfileForm] = useState({
    name: "",
    monthly_income: "",
    financial_preference: "Balanced",
    account_setting: "Standard",
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");

  const loadData = async () => {
  try {
    setDashboardError("");
    const me = await api.get("/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("ME", me.data);

    const monthParams = { params: { month: selectedMonth } };

    const dash = await api.get("/dashboard", {
      ...monthParams,
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("DASH", dash.data);

    const budget = await api.get("/budget", {
      ...monthParams,
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("BUDGET", budget.data);

    const expenseData = await api.get("/expenses", {
      ...monthParams,
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("EXPENSE", expenseData.data);

    const incomeData = await api.get("/income", {
      ...monthParams,
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("INCOME", incomeData.data);

    const goalData = await api.get("/goals", {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("GOALS", goalData.data);

    const notificationData = await api.get("/notifications", {
      headers: { Authorization: `Bearer ${token}` },
    });

    const profileData = await api.get("/profile", {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log("NOTIFY", notificationData.data);

    // Build the selected month's category budget view from the
    // already month-filtered budget and expense responses.
    // This keeps the budget section consistent with the selected month.
    const categories = [
      "Food",
      "Travel",
      "Shopping",
      "Education",
      "Entertainment",
      "Miscellaneous",
    ];

    const selectedCategorySummary = categories.map((category) => {
      const budgetAmount = budget.data
        .filter((item) => item.category === category)
        .reduce((sum, item) => sum + Number(item.amount || 0), 0);

      const expenseAmount = expenseData.data
        .filter((item) => item.category === category)
        .reduce((sum, item) => sum + Number(item.amount || 0), 0);

      return {
        category,
        budget: budgetAmount,
        spent: Math.min(expenseAmount, budgetAmount),
        actual_spent: expenseAmount,
      };
    });

    // State update
    setUser(me.data);
    setDashboard({
      ...dash.data,
      category_summary: selectedCategorySummary,
    });
    setBudgets(budget.data);
    setExpenses(expenseData.data);
    setIncomes(incomeData.data);
    setGoals(goalData.data);
    setNotifications(notificationData.data);
    setProfileForm({
      name: profileData.data.name || "",
      monthly_income: profileData.data.monthly_income ?? "",
      financial_preference: profileData.data.financial_preference || "Balanced",
      account_setting: profileData.data.account_setting || "Standard",
    });
    setLoadingAnalytics(true);

    try {
      // Main analytics data
      const analyticsRes = await api.get("/analytics", {
        ...monthParams,
        headers: { Authorization: `Bearer ${token}` },
      });

      // Monthly trends data
      const trendsRes = await api.get("/analytics/trends", {
        headers: { Authorization: `Bearer ${token}` },
      });

      const analyticsData = analyticsRes.data;

      // Convert backend response into the structure
      // expected by the Analytics Dashboard
      setAnalytics({
        total_income: analyticsData.summary?.income || 0,
        total_expense: analyticsData.summary?.expense || 0,
        remaining_budget: analyticsData.summary?.balance || 0,

        total_saved: Number(analyticsData.savings?.total_saved || 0),
        total_target: Number(analyticsData.savings?.total_target || 0),

        category_summary: (analyticsData.category_summary || []).map(
          (item) => ({
            category: item.category,
            spent: Number(item.amount || 0),
          })
        ),

        monthly_trends: trendsRes.data || [],
      });

      setAnalyticsError("");
    } catch (err) {
      console.error("ANALYTICS ERROR:", err.response?.data || err);
      setAnalyticsError("Failed to load analytics");
    } finally {
      setLoadingAnalytics(false);
    }

    const totalBudget = budget.data.reduce(
      (sum, item) => sum + Number(item.amount),
      0
    );

    setMonthlyBudget(totalBudget);
  } catch (err) {
    console.error("FAILED API:", err.response?.config?.url);
    console.error(err.response?.data || err);
    setDashboardError("Failed to load dashboard data. Please try again.");
  }
};

useEffect(() => {
  setBudgetForm((prev) => ({
    ...prev,
    month: selectedMonth,
  }));
  loadData();
}, [selectedMonth]);
const downloadPDF = async () => {
  const res = await fetch(`${api.defaults.baseURL}/report/pdf`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "BudgetBuddy_Report.pdf";
  a.click();

  window.URL.revokeObjectURL(url);
};

const downloadExcel = async () => {
  const res = await fetch(`${api.defaults.baseURL}/report/excel`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "BudgetBuddy_Report.xlsx";
  a.click();

  window.URL.revokeObjectURL(url);
};

const logout = () => {
  localStorage.removeItem("token");
  window.location.href = "/";
};

  const updateProfile = async () => {
    if (!profileForm.name.trim()) {
      alert("Name is required");
      return;
    }

    setProfileSaving(true);
    setProfileMessage("");

    try {
      const res = await api.put(
        "/profile",
        {
          name: profileForm.name.trim(),
          monthly_income:
            profileForm.monthly_income === ""
              ? null
              : Number(profileForm.monthly_income),
          financial_preference: profileForm.financial_preference,
          account_setting: profileForm.account_setting,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      setUser(res.data.profile);
      setProfileMessage("Profile updated successfully.");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update profile");
    } finally {
      setProfileSaving(false);
    }
  };

  /* ==========================================
  Add Expense
  ========================================== */

const addExpense = async () => {
  if (!expenseForm.title || !expenseForm.amount) {
    alert("Please fill all fields");
    return;
  }

  const amount = Number(expenseForm.amount);
  // Budget/category limits are enforced by the backend for the selected month.
  try {
    await api.post(
      "/expenses",
      {
        title: expenseForm.title,
        amount,
        category: expenseForm.category,
        date:
          selectedMonth === currentMonth
            ? new Date().toISOString().split("T")[0]
            : selectedMonth + "-01",
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    setExpenseForm({
      title: "",
      amount: "",
      category: "Food",
    });

    loadData();
    alert("Expense Added");
  } catch (err) {
    alert(err.response?.data?.detail || "Failed to add expense");
  }
};
  // =======================
  // Delete Expense
  // =======================
  const deleteExpense = async (expenseId) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this expense?"
    );

    if (!confirmDelete) return;

    try {
      await api.delete(`/expenses/${expenseId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      loadData();
      alert("Expense Deleted Successfully");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete expense");
    }
  };
  // =======================
  // Update Expense
  // =======================

  const updateExpense = async () => {
  try {
    await api.put(
      `/expenses/${editingExpense}`,
      {
        title: expenseForm.title,
        amount: Number(expenseForm.amount),
        category: expenseForm.category,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    setEditingExpense(null);
    setExpenseForm({
      title: "",
      amount: "",
      category: "Food",
    });

    loadData();
    alert("Expense Updated");
  } catch (err) {
    alert(err.response?.data?.detail || "Update Failed");
  }
};
  /* ==========================================
  Add Income
  ========================================== */

  const addIncome = async () => {
    if (!incomeForm.amount) {
      alert("Enter amount");
      return;
    }

    try {
      await api.post(
        "/income",
        {
          amount: Number(incomeForm.amount),
          source: incomeForm.source,
          description: incomeForm.description,
          date:
            selectedMonth === currentMonth
              ? new Date().toISOString().split("T")[0]
              : selectedMonth + "-01",
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setIncomeForm({
        amount: "",
        source: "Pocket Money",
        description: "",
      });

      loadData();
      alert("Income Added Successfully");
    } catch (err) {
      console.log(err.response?.data);
      alert(err.response?.data?.detail || "Failed to add income");
    }
  };
  // =======================
  // Delete Income
  // =======================
  const deleteIncome = async (incomeId) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this income?"
    );

    if (!confirmDelete) return;

    try {
      await api.delete(`/income/${incomeId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      loadData();
      alert("Income Deleted Successfully");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete income");
    }
  };
  // =======================
  // Update Income
  // =======================
  const updateIncome = async () => {
    try {
      await api.put(
        `/income/${editingIncome}`,
        {
          amount: Number(incomeForm.amount),
          source: incomeForm.source,
          description: incomeForm.description,
          date: new Date().toISOString().split("T")[0],
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setEditingIncome(null);

      setIncomeForm({
        amount: "",
        source: "Pocket Money",
        description: "",
      });

      loadData();
      alert("Income Updated Successfully");
    } catch (err) {
      alert(err.response?.data?.detail || "Update Failed");
    }
  };

  /* ==========================================
  Create / Update Budget
  ========================================== */

  const createBudget = async () => {
    if (!budgetForm.amount) {
      alert("Enter budget amount");
      return;
    }

    try {
      await api.post(
        "/budget",
        {
          category: budgetForm.category,
          amount: Number(budgetForm.amount),
          month: selectedMonth,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setBudgetForm({
        category: "Food",
        amount: "",
        month: selectedMonth,
      });

      loadData();
      alert("Budget Created");
    } catch {
      alert("Failed to create budget");
    }
  };
  const updateBudget = async () => {
  try {
    await api.put(
      `/budget/${editingBudget}`,
      {
        category: budgetForm.category,
        amount: Number(budgetForm.amount),
        month: selectedMonth,
      },
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    setEditingBudget(null);
    setBudgetForm({
      category: "Food",
      amount: "",
      month: selectedMonth,
    });

    loadData();
    alert("Budget Updated");
  } catch (err) {
    alert(err.response?.data?.detail || "Update Failed");
  }
};

  const deleteBudget = async (id) => {
    if (!window.confirm("Delete this budget?")) return;

    try {
      await api.delete(`/budget/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      loadData();
      alert("Budget Deleted");
    } catch {
      alert("Delete Failed");
    }
};
  const resetBudget = async () => {
    const confirmReset = window.confirm(
      "Reset all budgets? Income & Expenses will remain safe."
    );

    if (!confirmReset) return;

    try {
      await api.delete("/budget/reset", {
        params: { month: selectedMonth },
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setBudgets([]);
      setMonthlyBudget(0);

      loadData();

      alert("Budget Reset Successfully");
    } catch {
      alert("Failed to reset budget");
    }
  };
  const createGoal = async () => {
  if (!goalForm.goal_name || !goalForm.target_amount) {
    alert("Fill all fields");
    return;
  }

  await api.post(
    "/goals",
    {
      goal_name: goalForm.goal_name,
      target_amount: Number(goalForm.target_amount),
    },
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );

  setGoalForm({
    goal_name: "",
    target_amount: "",
    current_saved: "",
  });

  loadData();
};
  const saveGoal = async () => {
    await api.put(
      `/goals/${editingGoal}`,
      {
        goal_name: goalForm.goal_name,
        target_amount: Number(goalForm.target_amount),
      },
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    setEditingGoal(null);
    setGoalForm({
      goal_name: "",
      target_amount: "",
      current_saved: "",
    });

    loadData();
  };


  const updateProgress = async (id) => {
    if (goalForm.current_saved === "") {
      alert("Enter saved amount");
      return;
    }
    await api.patch(
      `/goals/${id}/progress`,
      {
        current_saved: Number(goalForm.current_saved),
      },
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );

    setGoalForm({
      goal_name: "",
      target_amount: "",
      current_saved: "",
    });

    loadData();
  };

  const deleteGoal = async (id) => {
    if (!window.confirm("Delete goal?")) return;

    await api.delete(`/goals/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    loadData();
  };


  /* ==========================================
  UI
  ========================================== */

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        background: "#F4F5FF",
        fontFamily: "Segoe UI",
      }}
    >
      {/* Sidebar */}
      <aside
        style={{
          width: 240,
          background: "linear-gradient(180deg,#5B3DF5,#7A4CFF)",
          color: "white",
          padding: 25,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div>
          <h2 style={{ margin: 0 }}>💰 BudgetBuddy</h2>

          <p style={{ opacity: 0.8, marginTop: 8 }}>
            Personal Finance Tracker
          </p>
        </div>

        <div style={{ marginTop: 35 }}>
          {["Dashboard", "Income", "Expenses", "Budget", "Savings", "Analytics", "Profile"].map((item) => (
            <div
              key={item}
              onClick={() => setActiveTab(item)}
              style={{
                padding: "14px 16px",
                borderRadius: 12,
                marginBottom: 12,
                background:
                  activeTab === item
                    ? "rgba(255,255,255,.25)"
                    : "rgba(255,255,255,.08)",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              {item}
            </div>
          ))}
        </div>

        <div style={{ marginTop: "auto" }}>
          <p style={{ fontSize: 13, opacity: 0.8 }}>
            Logged in as
          </p>

          <strong>{user.name}</strong>
        </div>
      </aside>

{/* Main Content */}
<main style={{ flex: 1, padding: 30 }}>
  {dashboardError && (
  <div
    style={{
      marginBottom: 20,
      padding: 14,
      background: "#FEE2E2",
      color: "#991B1B",
      borderRadius: 10,
      fontWeight: 600,
    }}
  >
    ⚠️ {dashboardError}
  </div>
)}
  {/* Header */}
  <div
    style={{
      background: "white",
      borderRadius: 18,
      padding: 22,
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      boxShadow: "0 8px 20px rgba(0,0,0,.06)",
    }}
  >
    <div>
      <h1 style={{ margin: 0 }}>
        Hello, {user.name} 👋
      </h1>

      <p style={{ color: "#666", marginTop: 6 }}>
        {user.email}
      </p>
    </div>

    <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
      <strong>📅 {selectedMonth}</strong>
      <input
        type="month"
        value={selectedMonth}
        onChange={(e) => setSelectedMonth(e.target.value)}
        style={{ ...inputStyle, width: 155 }}
      />
      <button
        onClick={downloadPDF}
        style={headerBtn}
      >
        📄 PDF
      </button>

      <button
        onClick={downloadExcel}
        style={headerBtn}
      >
        📊 Excel
      </button>

      <button onClick={logout} style={headerBtn}>
        Logout
      </button>
    </div>
  </div>
        {/* Notifications */}
        {notifications.length > 0 && (
          <div style={{ marginTop: 20 }}>
            {notifications.map((n) => (
              <div
                key={n.id}
                style={{
                  background: n.is_read ? "#F3F4F6" : "#EEF2FF",
                  borderLeft: `5px solid ${
                    n.type === "budget" ? "#F59E0B" : "#22C55E"
                  }`,
                  padding: 12,
                  borderRadius: 8,
                  marginBottom: 10,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div>
                  <strong>{n.message}</strong>
                  <p style={{ fontSize: 12, color: "#666", margin: 0 }}>
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </div>

                {!n.is_read && (
                  <button
                    onClick={async () => {
                      await api.patch(
                        `/notifications/${n.id}/read`,
                        {},
                        { headers: { Authorization: `Bearer ${token}` } }
                      );
                      setNotifications((prev) =>
                        prev.filter((item) => item.id !== n.id)
                      );
                    }}
                    style={{
                      background: "#5B3DF5",
                      color: "#fff",
                      border: "none",
                      borderRadius: 6,
                      padding: "6px 12px",
                      cursor: "pointer",
                    }}
                  >
                    Mark Read
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Dashboard Section starts here */}

        {activeTab === "Dashboard" && (
          <>
            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fit, minmax(180px,1fr))",
                gap: 18,
                marginTop: 25,
              }}
            >
              <Card
                icon="💳"
                title="Total Balance"
                value={`₹${Math.max(0, dashboard.remaining_amount)}`}
              />

              <Card
                icon="📈"
                title="Income"
                value={`₹${dashboard.total_income}`}
              />

              <Card
                icon="💸"
                title="Expenses"
                value={`₹${dashboard.total_expense}`}
              />

              <Card
                icon="🎯"
                title="Budget"
                value={`₹${monthlyBudget}`}
              />
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "2fr 1fr",
                gap: 20,
                marginTop: 25,
              }}
            >
              {/* Remaining code continues... */}
              {/* Transactions */}
<div
  style={{
    background: "white",
    borderRadius: 18,
    padding: 20,
    boxShadow: "0 8px 20px rgba(0,0,0,.05)",
  }}
>
  <div
    style={{
      display: "flex",
      justifyContent: "space-between",
      marginBottom: 15,
    }}
  >
    <h3>Recent Transactions</h3>
    <span style={{ color: "#777" }}>{selectedMonth}</span>
  </div>

  <table
    style={{
      width: "100%",
      borderCollapse: "collapse",
    }}
  >
    <thead>
      <tr>
        <th align="left">Type</th>
        <th align="left">Title</th>
        <th align="left">Amount</th>
      </tr>
    </thead>

    <tbody>
      {dashboard.recent_activity.map((tx, i) => (
        <tr key={i}>
          <td
            style={{
              padding: "14px 0",
              borderTop: "1px solid #eee",
            }}
          >
            {tx.type === "Income" ? "💰" : "💸"} {tx.type}
          </td>

          <td style={{ borderTop: "1px solid #eee" }}>
            {tx.title}
          </td>

          <td
            style={{
              borderTop: "1px solid #eee",
              fontWeight: 700,
              color:
                tx.type === "Income"
                  ? "#16A34A"
                  : "#DC2626",
            }}
          >
            {tx.type === "Income" ? "+" : "-"}₹{tx.amount}
          </td>
        </tr>
      ))}
    </tbody>
  </table>
</div>

{/* Budget Circle */}
<div
  style={{
    background: "white",
    borderRadius: 18,
    padding: 20,
    textAlign: "center",
    boxShadow: "0 8px 20px rgba(0,0,0,.05)",
  }}
>
  <h3>Budget Status</h3>

  <div
    style={{
      width: 140,
      height: 140,
      margin: "20px auto",
      borderRadius: "50%",
      background: `conic-gradient(#5B3DF5 ${
        monthlyBudget
          ? Math.min(
              (dashboard.total_expense / monthlyBudget) * 100,
              100
            )
          : 0
      }%, #E5E7EB 0%)`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    }}
  >
    <div
      style={{
        width: 95,
        height: 95,
        borderRadius: "50%",
        background: "white",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: 700,
        color: "#5B3DF5",
      }}
    >
      {monthlyBudget
          ? `${Math.min(
              Math.round(
                (dashboard.total_expense / monthlyBudget) * 100
              ),
              100
            )}%`
          : "0%"}
    </div>
  </div>

  <p>Spent: ₹{dashboard.total_expense}</p>
  <p>Budget: ₹{monthlyBudget}</p>
</div>

</div>
</>)}

{/* ================= INCOME ================= */}

{activeTab === "Income" && (
  <div
    style={{
      background: "white",
      padding: 25,
      borderRadius: 18,
      marginTop: 25,
    }}
  >
    <h2>Income Manager</h2>

    <div
      style={{
        display: "grid",
        gap: 15,
        marginTop: 20,
      }}
    >
      <input
        type="number"
        placeholder="Amount"
        value={incomeForm.amount}
        onChange={(e) =>
          setIncomeForm({
            ...incomeForm,
            amount: e.target.value,
          })
        }
        style={inputStyle}
      />

      <select
        value={incomeForm.source}
        onChange={(e) =>
          setIncomeForm({
            ...incomeForm,
            source: e.target.value,
          })
        }
        style={inputStyle}
      >
        <option>Pocket Money</option>
        <option>Scholarship</option>
        <option>Freelance Income</option>
      </select>

      <input
        placeholder="Description"
        value={incomeForm.description}
        onChange={(e) =>
          setIncomeForm({
            ...incomeForm,
            description: e.target.value,
          })
        }
        style={inputStyle}
      />

      <button
        onClick={editingIncome ? updateIncome : addIncome}
        style={{
          height: 48,
          background: editingIncome ? "#2563EB" : "#5B3DF5",
          color: "white",
          border: "none",
          borderRadius: 10,
          fontWeight: 600,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
        }}
      >
        {editingIncome ? "✏️ Update Income" : "➕ Add Income"}
      </button>
    </div>

    <h3 style={{ marginTop: 35 }}>Income History</h3>

{incomes.length === 0 ? (
  <p style={{ color: "#777" }}>No income added yet.</p>
) : (
  incomes.map((inc) => (
    <div
      key={inc.id}
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "14px 0",
        borderBottom: "1px solid #eee",
      }}
    >
      <div>
        <strong>{inc.source}</strong>
        <p style={{ margin: "4px 0 0", color: "#666", fontSize: 13 }}>
          {inc.description || "Income"}
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <strong style={{ color: "#16A34A" }}>
          +₹{inc.amount}
        </strong>

        <button
          onClick={() => deleteIncome(inc.id)}
          style={{
            background: "#DC2626",
            color: "#fff",
            border: "none",
            padding: "6px 12px",
            borderRadius: 8,
            cursor: "pointer",
          }}
        >
          Delete
        </button>
        <button
          onClick={() => {
            setEditingIncome(inc.id);
            setIncomeForm({
              amount: inc.amount,
              source: inc.source,
              description: inc.description,
          });
        }}
        style={{
          background: "#2563EB",
          color: "#fff",
          border: "none",
          padding: "6px 12px",
          borderRadius: 8,
          cursor: "pointer",
          fontWeight: 600,
        }}
      >
        ✏️ Edit
      </button>
      </div>
    </div>
  ))
)}
  </div>
)}
{/* ================= EXPENSE ================= */}

{activeTab === "Expenses" && (
  <div
    style={{
      background: "white",
      borderRadius: 18,
      padding: 25,
      marginTop: 25,
    }}
  >
    <h2>Add Expense</h2>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 15, alignItems: "center", marginTop: 10 }}>
      <div>
        <label style={{ display: "block", color: "#666", marginBottom: 6 }}>Expense Month</label>
        <input type="month" value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)} style={inputStyle} />
      </div>
      <div style={{ color: "#5B3DF5", fontWeight: 600, paddingTop: 24 }}>
        Budget automatically synced to {selectedMonth}
      </div>
    </div>
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 15,
        marginTop: 20,
      }}
    >
      <input
        placeholder="Expense Title"
        value={expenseForm.title}
        onChange={(e) =>
          setExpenseForm({
            ...expenseForm,
            title: e.target.value,
          })
        }
        style={inputStyle}
      />

      <input
        type="number"
        placeholder="Amount"
        value={expenseForm.amount}
        onChange={(e) =>
          setExpenseForm({
            ...expenseForm,
            amount: e.target.value,
          })
        }
        style={inputStyle}
      />

      <select
        value={expenseForm.category}
        onChange={(e) =>
          setExpenseForm({
            ...expenseForm,
            category: e.target.value,
          })
        }
        style={inputStyle}
      >
        <option>Food</option>
        <option>Travel</option>
        <option>Shopping</option>
        <option>Education</option>
        <option>Entertainment</option>
        <option>Miscellaneous</option>
      </select>

      <button
        onClick={editingExpense ? updateExpense : addExpense}
        style={{
          gridColumn: "1 / -1",
          height: 48,
          background: editingExpense ? "#2563EB" : "#5B3DF5",
          color: "white",
          border: "none",
          borderRadius: 10,
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        {editingExpense ? "Update Expense" : "Add Expense"}
      </button>
    </div>

    <h3 style={{ marginTop: 35 }}>Expense History</h3>

{expenses.length === 0 ? (
  <p style={{ color: "#777" }}>No expenses added yet.</p>
) : (
  expenses.map((exp) => (
    <div
      key={exp.id}
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "14px 0",
        borderBottom: "1px solid #eee",
      }}
    >
      <div>
        <strong>{exp.title}</strong>
        <p
          style={{
            margin: "4px 0 0",
            color: "#666",
            fontSize: 13,
          }}
        >
          {exp.category}
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <strong style={{ color: "#DC2626" }}>
          -₹{exp.amount}
        </strong>
        <button
          onClick={() => {
            setEditingExpense(exp.id);
            setExpenseForm({
              title: exp.title,
              amount: exp.amount,
              category: exp.category,
            });
          }}
          style={{
            background: "#2563EB",
            color: "#fff",
            border: "none",
            padding: "6px 12px",
            borderRadius: 8,
            cursor: "pointer",
          }}
        >
          Edit
        </button>

        <button
          onClick={() => deleteExpense(exp.id)}
          style={{
            background: "#DC2626",
            color: "#fff",
            border: "none",
            padding: "6px 12px",
            borderRadius: 8,
            cursor: "pointer",
          }}
        >
          Delete
        </button>
      </div>
    </div>
  ))
)}

  </div>

)}

{/* ================= BUDGET ================= */}

{activeTab === "Budget" && (
  <div
    style={{
      background: "white",
      borderRadius: 18,
      padding: 25,
      marginTop: 25,
      boxShadow: "0 8px 20px rgba(0,0,0,.05)",
    }}
  >
    <h2 style={{ marginBottom: 5 }}>Budget Planner</h2>

    <p style={{ color: "#666", marginBottom: 20 }}>
      Create monthly category-wise budget
    </p>

    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 15,
      }}
    >
      <select
        value={budgetForm.category}
        onChange={(e) =>
          setBudgetForm({
            ...budgetForm,
            category: e.target.value,
          })
        }
        style={inputStyle}
      >
        <option>Food</option>
        <option>Travel</option>
        <option>Shopping</option>
        <option>Education</option>
        <option>Entertainment</option>
        <option>Miscellaneous</option>
      </select>
      <input
        type="number"
        placeholder="Budget Amount"
        value={budgetForm.amount}
        onChange={(e) =>
          setBudgetForm({
            ...budgetForm,
            amount: e.target.value,
          })
        }
        style={inputStyle}
      />

      <div
        style={{
          ...inputStyle,
          display: "flex",
          alignItems: "center",
          background: "#F3F4F6",
          color: "#374151",
          fontWeight: 600,
        }}
      >
        Selected Month: {selectedMonth}
      </div>

      <button
        onClick={editingBudget ? updateBudget : createBudget}
        style={{
          gridColumn: "1 / -1",
          height: 48,
          background: editingBudget ? "#2563EB" : "#5B3DF5",
          color: "white",
          border: "none",
          borderRadius: 10,
          fontWeight: 600,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
        }}
      >
        {editingBudget ? "Update Budget" : "Create Budget"}
      </button>
      </div>
      {editingBudget && (
        <button
          onClick={() => {
            setEditingBudget(null);
            setBudgetForm({
              category: "Food",
              amount: "",
              month: selectedMonth,
            });
          }}
          style={{
            gridColumn: "1 / -1",
            height: 44,
            background: "#E5E7EB",
            color: "#111827",
            border: "none",
            borderRadius: 10,
            fontWeight: 600,
            cursor: "pointer",
            marginTop: 8,
          }}
        >
          Cancel
        </button>
      )}
      <button
        onClick={resetBudget}
        style={{
          width: "100%",
          height: 44,
          background: "#DC2626",
          color: "#fff",
          border: "none",
          borderRadius: 10,
          fontWeight: 600,
          cursor: "pointer",
          marginTop: 10,
        }}
      >
  Reset Selected Month Budgets
</button>

    {/* Current Budget Summary */}
    <div
      style={{
        marginTop: 30,
        background: "#F5F3FF",
        borderRadius: 14,
        padding: 20,
      }}
    >
      <h3
        style={{
          color: "#5B3DF5",
          marginTop: 0,
        }}
      >
        Current Budget
      </h3>
      {dashboard.remaining_amount <= monthlyBudget * 0.2 &&
        monthlyBudget > 0 && (
          <div
            style={{
              background: "#FEF3C7",
              color: "#92400E",
              padding: 12,
              borderRadius: 10,
              margin: "12px 0",
              fontWeight: 600,
            }}
          >
            ⚠️ Budget almost exhausted! Remaining ₹
            {Math.max(0, dashboard.remaining_amount)}
          </div>
        )}

      <h1
        style={{
          color: "#5B3DF5",
          margin: "10px 0",
        }}
      >
        ₹{monthlyBudget}
      </h1>

      <hr
        style={{
          borderColor: "#E5E7EB",
        }}
      />

      <div style={{ lineHeight: 2 }}>
        <p>
          💰 Total Budget: <strong>₹{monthlyBudget}</strong>
        </p>

        <p>
          💸 Expenses:{" "}
          <strong>₹{dashboard.total_expense}</strong>
        </p>

        <p>
          💵 Remaining:{" "}
          <strong>
            ₹{Math.max(0, dashboard.remaining_amount)}
          </strong>
        </p>
      </div>
    </div>
    {/* Category Wise Budget */}
    <h3 style={{ marginTop: 30 }}>Category Wise Budget</h3>

    {dashboard.category_summary?.map((item) => {
      const percent = item.budget
        ? Math.min((item.spent / item.budget) * 100, 100)
        : 0;

      const color =
        percent >= 100
          ? "#EF4444"
          : percent >= 80
          ? "#F59E0B"
          : "#22C55E";

      return (
        <div key={item.category} style={{ marginTop: 18 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <strong>{item.category}</strong>
            <strong>₹{item.budget}</strong>
          </div>

          <div
            style={{
              height: 10,
              background: "#E5E7EB",
              borderRadius: 10,
              marginTop: 8,
            }}
          >
            <div
              style={{
                width: `${percent}%`,
                height: "100%",
                background: color,
                borderRadius: 10,
              }}
            />
          </div>

          <p
            style={{
              fontSize: 13,
              color: "#666",
              textAlign: "right",
            }}
          >
            ₹{Math.min(item.actual_spent, item.budget)} / ₹{item.budget}
          </p>
        </div>
      );
    })}

    <h3 style={{ marginTop: 30 }}>Budget History</h3>

{budgets.length === 0 ? (
  <p style={{ color: "#777" }}>No budgets created yet.</p>
) : (
  budgets.map((bud) => (
    <div
      key={bud.id}
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "14px 0",
        borderBottom: "1px solid #eee",
      }}
    >
      <div>
        <strong>{bud.category}</strong>
        <p
          style={{
            margin: "4px 0 0",
            color: "#666",
            fontSize: 13,
          }}
        >
          {new Date(bud.month + "-01").toLocaleDateString("en-IN", {
            month: "long",
            year: "numeric",
          })}
        </p>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <strong style={{ color: "#5B3DF5" }}>
          ₹{bud.amount}
        </strong>

        <button
          onClick={() => {
            setEditingBudget(bud.id);
            setBudgetForm({
              category: bud.category,
              amount: bud.amount,
              month: bud.month,
            });
          }}
          style={{
            background: "#2563EB",
            color: "#fff",
            border: "none",
            padding: "6px 12px",
            borderRadius: 8,
            cursor: "pointer",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          ✏️ Edit
        </button>

        <button
          onClick={() => deleteBudget(bud.id)}
          style={{
            background: "#DC2626",
            color: "#fff",
            border: "none",
            padding: "6px 12px",
            borderRadius: 8,
            cursor: "pointer",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          🗑 Delete
        </button>
      </div>
    </div>
  ))
)}
  </div>
)}
{/* ================= SAVINGS ================= */}

{activeTab === "Savings" && (
  <div
    style={{
      background: "white",
      borderRadius: 18,
      padding: 25,
      marginTop: 25,
    }}
  >
    <h2>Savings Goals</h2>

    {/* Goal Form */}
    <div style={{ display: "grid", gap: 12, marginTop: 20 }}>
      <input
        placeholder="Goal Name"
        value={goalForm.goal_name}
        onChange={(e) =>
          setGoalForm({ ...goalForm, goal_name: e.target.value })
        }
        style={inputStyle}
      />

      <input
        type="number"
        placeholder="Target Amount"
        value={goalForm.target_amount}
        onChange={(e) =>
          setGoalForm({
            ...goalForm,
            target_amount: e.target.value,
          })
        }
        style={inputStyle}
      />

      <button
        onClick={editingGoal ? saveGoal : createGoal}
        style={{
          height: 45,
          background: editingGoal ? "#2563EB" : "#5B3DF5",
          color: "#fff",
          border: "none",
          borderRadius: 10,
          fontWeight: 600,
        }}
      >
        {editingGoal ? "Update Goal" : "Create Goal"}
      </button>
    </div>

  <h3 style={{ marginTop: 30 }}>Your Goals</h3>

{goals.length === 0 ? (
  <p style={{ color: "#777" }}>No savings goals yet.</p>
) : (
  goals.map((goal) => (
    <div
      key={goal.id}
      style={{
        padding: 18,
        border: "1px solid #eee",
        borderRadius: 12,
        marginTop: 15,
      }}
    >
      <strong>{goal.goal_name}</strong>

      <p>
        ₹{goal.current_saved} / ₹{goal.target_amount}
      </p>

      <div
        style={{
          height: 10,
          background: "#E5E7EB",
          borderRadius: 10,
        }}
      >
        <div
          style={{
            width: `${Math.min(
              (goal.current_saved / goal.target_amount) * 100,
              100
            )}%`,
            height: "100%",
            background: "#5B3DF5",
            borderRadius: 10,
          }}
        />
      </div>

      <p style={{ fontSize: 13 }}>
        {Math.round(
          (goal.current_saved / goal.target_amount) * 100
        )}
        % Completed
      </p>

      <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
        <input
          type="number"
          placeholder="Saved Amount"
          value={goalForm.current_saved}
          onChange={(e) =>
            setGoalForm({
              ...goalForm,
              current_saved: e.target.value,
            })
          }
          style={{ ...inputStyle, flex: 1 }}
        />

        <button
          onClick={() => updateProgress(goal.id)}
          style={{
            background: "#16A34A",
            color: "#fff",
            border: "none",
            padding: "0 18px",
            borderRadius: 8,
          }}
        >
          Update
        </button>

        <button
          onClick={() => deleteGoal(goal.id)}
          style={{
            background: "#DC2626",
            color: "#fff",
            border: "none",
            padding: "0 18px",
            borderRadius: 8,
          }}
        >
          Delete
        </button>
      </div>
    </div>
  ))
)}
  </div>
)}
{activeTab === "Profile" && (
  <div
    style={{
      background: "white",
      borderRadius: 18,
      padding: 25,
      marginTop: 25,
      maxWidth: 760,
      boxShadow: "0 8px 20px rgba(0,0,0,.05)",
    }}
  >
    <h2>Profile Management</h2>
    <p style={{ color: "#666", marginTop: 6 }}>
      Manage your personal details, monthly income and financial preferences.
    </p>

    {profileMessage && (
      <div
        style={{
          marginTop: 18,
          padding: 12,
          borderRadius: 10,
          background: "#DCFCE7",
          color: "#166534",
          fontWeight: 600,
        }}
      >
        ✅ {profileMessage}
      </div>
    )}

    <div style={{ display: "grid", gap: 15, marginTop: 22 }}>
      <div>
        <label style={{ display: "block", marginBottom: 7, fontWeight: 600 }}>
          Full Name
        </label>
        <input
          style={inputStyle}
          value={profileForm.name}
          onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })}
          placeholder="Your name"
        />
      </div>

      <div>
        <label style={{ display: "block", marginBottom: 7, fontWeight: 600 }}>
          Email
        </label>
        <input
          style={{ ...inputStyle, background: "#F3F4F6" }}
          value={user.email || ""}
          disabled
        />
      </div>

      <div>
        <label style={{ display: "block", marginBottom: 7, fontWeight: 600 }}>
          Monthly Income
        </label>
        <input
          type="number"
          min="0"
          style={inputStyle}
          value={profileForm.monthly_income}
          onChange={(e) => setProfileForm({ ...profileForm, monthly_income: e.target.value })}
          placeholder="e.g. 20000"
        />
      </div>

      <div>
        <label style={{ display: "block", marginBottom: 7, fontWeight: 600 }}>
          Financial Preference
        </label>
        <select
          style={inputStyle}
          value={profileForm.financial_preference}
          onChange={(e) => setProfileForm({ ...profileForm, financial_preference: e.target.value })}
        >
          <option>Conservative</option>
          <option>Balanced</option>
          <option>Aggressive Saving</option>
        </select>
      </div>

      <div>
        <label style={{ display: "block", marginBottom: 7, fontWeight: 600 }}>
          Account Setting
        </label>
        <select
          style={inputStyle}
          value={profileForm.account_setting}
          onChange={(e) => setProfileForm({ ...profileForm, account_setting: e.target.value })}
        >
          <option>Standard</option>
          <option>Privacy Focused</option>
          <option>Notifications Enabled</option>
        </select>
      </div>

      <button
        onClick={updateProfile}
        disabled={profileSaving}
        style={{
          height: 48,
          background: profileSaving ? "#9CA3AF" : "#5B3DF5",
          color: "white",
          border: "none",
          borderRadius: 10,
          fontWeight: 600,
          cursor: profileSaving ? "not-allowed" : "pointer",
        }}
      >
        {profileSaving ? "Saving..." : "Save Profile"}
      </button>
    </div>

    <div
      style={{
        marginTop: 25,
        padding: 16,
        background: "#F5F3FF",
        borderRadius: 12,
      }}
    >
      <strong>Account Role:</strong> {user.role || "student"}
    </div>
  </div>
)}

{activeTab === "Analytics" && (
  <div>
    <h2>Analytics Dashboard</h2>

    {loadingAnalytics && <p>Loading analytics...</p>}

    {analyticsError && (
      <p style={{ color: "red" }}>{analyticsError}</p>
    )}
  {!loadingAnalytics &&
  analytics &&
  analytics.total_income === 0 &&
  analytics.total_expense === 0 && (
    <div
      style={{
        marginTop: 30,
        background: "#fff",
        padding: 30,
        borderRadius: 15,
        textAlign: "center",
      }}
    >
      <h3>No financial data</h3>
      <p>Add income and expenses to view analytics.</p>
    </div>
)}

  {!loadingAnalytics &&
    analytics &&
    (analytics.total_income > 0 || analytics.total_expense > 0) && (
  <>
    {/* Summary Cards */}
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(4,1fr)",
        gap: 20,
        marginTop: 20,
      }}
    >
      <Card icon="💰" title="Income" value={`₹${analytics.total_income}`} />
      <Card icon="💸" title="Expense" value={`₹${analytics.total_expense}`} />
      <Card
        icon="💵"
        title="Balance"
        value={`₹${analytics.remaining_budget}`}
      />
      <Card
        icon="🏦"
        title="Savings"
        value={`₹${analytics.total_saved}`}
      />
    </div>

    {/* Charts */}
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 25,
        marginTop: 35,
      }}
    >
      {/* Pie Chart */}
      <div
        style={{
          background: "#fff",
          borderRadius: 15,
          padding: 20,
          boxShadow: "0 5px 15px rgba(0,0,0,.05)",
        }}
      >
        <h3>Category Spending</h3>

{analytics.category_summary.some((item) => item.spent > 0) ? (
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={analytics.category_summary.filter((item) => item.spent > 0)}
                dataKey="spent"
                nameKey="category"
                outerRadius={90}
                label
              >
                {analytics.category_summary
                  .filter((item) => item.spent > 0)
                  .map((_, i) => (
                    <Cell
                      key={i}
                      fill={
                        [
                          "#5B3DF5",
                          "#22C55E",
                          "#F59E0B",
                          "#EF4444",
                          "#0EA5E9",
                          "#A855F7",
                        ][i % 6]
                      }
                    />
                  ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div
            style={{
              height: 260,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              textAlign: "center",
              color: "#777",
            }}
          >
            <div>
              <div style={{ fontSize: 36 }}>📊</div>
              <strong>No spending in {selectedMonth}</strong>
              <p style={{ marginTop: 8 }}>
                Add an expense to see category-wise spending.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Monthly Category-wise Expense Chart */}
      <div style={{ gridColumn: "1 / -1", background: "#fff", borderRadius: 15, padding: 20, boxShadow: "0 5px 15px rgba(0,0,0,.05)" }}>
        <h3>Monthly Category-wise Expenses</h3>
        <p style={{ color: "#666", marginTop: 0 }}>Every month stays separate. Categories without expenses remain ₹0.</p>
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={analytics.monthly_trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip formatter={(value) => "₹" + value} />
            <Bar dataKey="Food" stackId="expenses" fill="#5B3DF5" />
            <Bar dataKey="Travel" stackId="expenses" fill="#22C55E" />
            <Bar dataKey="Shopping" stackId="expenses" fill="#F59E0B" />
            <Bar dataKey="Education" stackId="expenses" fill="#EF4444" />
            <Bar dataKey="Entertainment" stackId="expenses" fill="#0EA5E9" />
            <Bar dataKey="Miscellaneous" stackId="expenses" fill="#A855F7" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Monthly Income vs Expense */}
      <div style={{ gridColumn: "1 / -1", background: "#fff", borderRadius: 15, padding: 20, boxShadow: "0 5px 15px rgba(0,0,0,.05)" }}>
        <h3>Monthly Income vs Expense</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={analytics.monthly_trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="income" fill="#22C55E" />
            <Bar dataKey="expense" fill="#EF4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    {/* Savings Progress */}
    <div
      style={{
        marginTop: 30,
        background: "#fff",
        borderRadius: 15,
        padding: 20,
        boxShadow: "0 5px 15px rgba(0,0,0,.05)",
      }}
    >
      <h3>Savings Progress</h3>

      <div
        style={{
          height: 18,
          background: "#E5E7EB",
          borderRadius: 20,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${
              analytics.total_target > 0
                ? Math.min(
                    (analytics.total_saved / analytics.total_target) * 100,
                    100
                  )
                : 0
            }%`,
            height: "100%",
            background: "#5B3DF5",
          }}
        />
      </div>

      <p style={{ marginTop: 10 }}>
        ₹{analytics.total_saved} / ₹{analytics.total_target}
      </p>
    </div>
  </>
)}
  </div>
)}
      </main>
    </div>
  );
}

function Card({ icon, title, value }) {
  return (
    <div
      style={{
        background: "white",
        borderRadius: 16,
        padding: 20,
        boxShadow: "0 8px 20px rgba(0,0,0,.05)",
      }}
    >
      <p style={{ color: "#666", marginBottom: 12 }}>
        {icon} {title}
      </p>

      <h2 style={{ color: "#5B3DF5", margin: 0 }}>
        {value}
      </h2>
    </div>
  );
}
const headerBtn = {
  background: "#5B3DF5",
  color: "#fff",
  border: "none",
  padding: "10px 16px",
  borderRadius: 10,
  cursor: "pointer",
  fontWeight: 600,
};

const inputStyle = {
  height: 45,
  borderRadius: 10,
  border: "1px solid #DDD",
  padding: "0 12px",
  outline: "none",
  fontSize: 15,
};