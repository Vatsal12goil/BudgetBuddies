# 💰 BudgetBuddy

### Your Smart Personal Finance Companion

A modern full-stack expense and income management application built with **React + FastAPI + SQLite**. BudgetBuddy helps users track expenses, manage multiple income sources, monitor their financial health, and visualize their spending through a secure dashboard.

---

## ✨ Features

* 🔐 JWT Authentication (Login & Register)
* 💸 Expense Management
* 💵 Income Management
* 📊 Financial Dashboard Summary
* 👤 User-specific Data Isolation
* ⚡ RESTful API Architecture
* 🎨 Modern React UI

---

## 🛠 Tech Stack

| Frontend     | Backend | Database | Auth       |
| ------------ | ------- | -------- | ---------- |
| React (Vite) | FastAPI | SQLite   | JWT Bearer |

---

## 📂 Project Structure

```text
BudgetBuddy/
│
├── app/
│   ├── main.py          # FastAPI routes
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── auth.py          # JWT authentication
│   └── database.py
│
├── client/
│   ├── src/
│   │   ├── pages/
│   │   ├── api.js
│   │   └── styles.css
│   └── vite.config.js
│
└── README.md
```

---

## 🚀 Current Modules

### Authentication

* User Registration
* Secure Login
* JWT Token Authorization
* Protected APIs

### Expense Module

* Add Expense
* View Expenses
* User-wise Expense Storage

### Income Module

Supported income sources:

* Pocket Money
* Scholarship
* Freelance Income

Operations:

* Create
* Read
* Update
* Delete

### Dashboard Summary

Automatically calculates:

```text
Total Income
      -
Total Expenses
      =
Remaining Balance
```

Also provides recent financial activity.

---

## 📡 REST APIs

| Method | Endpoint       | Description       |
| ------ | -------------- | ----------------- |
| POST   | `/register`    | Register user     |
| POST   | `/login`       | Login & JWT       |
| GET    | `/me`          | Current user      |
| POST   | `/expenses`    | Add expense       |
| GET    | `/expenses`    | View expenses     |
| POST   | `/income`      | Add income        |
| GET    | `/income`      | Income history    |
| PUT    | `/income/{id}` | Update income     |
| DELETE | `/income/{id}` | Delete income     |
| GET    | `/dashboard`   | Financial summary |

---

## 🧪 Validation Tested

* ✅ Valid income creation
* ✅ Invalid income source
* ✅ Missing required fields
* ✅ Unauthorized access (JWT)
* ✅ Invalid record handling
* ✅ User ownership enforcement

---

## ▶️ Run Locally

### Backend

```bash
cd BudgetBuddy
venv\Scripts\activate
uvicorn app.main:app --reload
```

### Frontend

```bash
cd client
npm install
npm run dev
```

Open:

* Frontend → `http://localhost:5173`
* Swagger → `http://127.0.0.1:8000/docs`

---

## 🎯 Roadmap

* [x] Authentication
* [x] Expense Tracking
* [x] Income Management
* [x] Dashboard Summary API
* [ ] Expense Categories
* [ ] Monthly Budget Module
* [ ] Analytics & Charts
* [ ] PostgreSQL Migration

---

## 👨‍💻 Author

**Vatsal Goil**

Cyber Security • Full Stack Development • Python • React • FastAPI

> *“Track every rupee. Understand every decision. Grow with every saving.”*
