# 💰 BudgetBuddy

### Smart Personal Finance Management

BudgetBuddy is a full-stack personal finance management application built with **React + Vite** on the frontend and **FastAPI + SQLAlchemy** on the backend. It helps users manage income and expenses, create category budgets, track savings goals, monitor notifications, analyze financial trends, and generate PDF/Excel reports.

---

## ✨ Features

- 🔐 JWT authentication with protected APIs
- 👤 User-specific data isolation
- 💸 Expense CRUD management
- 💵 Income CRUD management
- 🏷️ Expense categories
- 💰 Category-based monthly budgets
- 🚨 Budget utilization and threshold notifications
- 🎯 Savings goals and progress tracking
- 🔔 Notification management and mark-as-read
- 📊 Dashboard financial summary
- 📈 Analytics and spending trends
- 🥧 Category distribution charts
- 📅 Monthly income/expense trends
- 📄 PDF financial reports
- 📊 Excel financial reports
- 🩺 Backend health endpoint
- 🌐 Environment-based API URL and CORS configuration
- 🗃️ Alembic database migrations
- 🐘 PostgreSQL-ready database configuration

---

## 🛠️ Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, Axios, React Router, Recharts |
| Backend | FastAPI, Python |
| ORM | SQLAlchemy |
| Database | SQLite (local), PostgreSQL-ready |
| Authentication | JWT Bearer Tokens, bcrypt |
| Migrations | Alembic |
| Reports | ReportLab, openpyxl |
| Deployment Configuration | Environment variables, CORS |

---

## 📂 Project Structure

```text
BudgetBuddy/
│
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   └── database.py
│
├── alembic/
│   ├── env.py
│   └── versions/
│
├── client/
│   ├── src/
│   │   ├── pages/
│   │   ├── api.js
│   │   └── ...
│   ├── .env.example
│   └── vite.config.js
│
├── .env.example
├── requirements.txt
├── alembic.ini
└── README.md
```

---

## 🔐 Authentication

BudgetBuddy uses JWT bearer authentication.

- User registration
- Login and token generation
- Protected endpoints
- Current-user endpoint
- User ownership checks for financial records
- Configurable JWT algorithm and token expiry through environment variables

---

## 💸 Finance Modules

### Expenses

Users can:

- Add expenses
- View expenses
- Update expenses
- Delete expenses
- Organize expenses by category and date

### Income

Users can:

- Add income
- View income history
- Update income
- Delete income
- Track income sources

### Budgets

Users can create monthly category budgets and monitor utilization against spending.

Budget notifications are generated around configured utilization thresholds, including 80% and 100% usage.

### Savings Goals

Users can create savings goals, update saved amounts, track progress, and identify completed goals.

---

## 📊 Dashboard & Analytics

The dashboard provides a financial overview including:

- Total income
- Total expenses
- Remaining balance
- Recent financial activity
- Savings progress
- Budget utilization

Analytics includes:

- Category-wise expense distribution
- Monthly income vs. expense trends
- Financial trend data
- Real API-backed charts

---

## 📄 Reports

Authenticated users can generate:

- PDF financial reports
- Excel financial reports

Report requests use the configured backend API URL rather than a hardcoded production endpoint.

---

## 📡 Important REST APIs

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/register` | Register a user |
| POST | `/login` | Login and receive JWT |
| GET | `/me` | Get current user |
| GET | `/health` | Backend health check |
| GET/POST/PUT/DELETE | `/expenses` | Expense management |
| GET/POST/PUT/DELETE | `/income` | Income management |
| GET/POST/PUT/DELETE | `/budgets` | Budget management |
| GET/POST/PUT/DELETE | `/savings-goals` | Savings goal management |
| GET | `/notifications` | User notifications |
| GET | `/analytics` | Analytics summary |
| GET | `/analytics/trends` | Trend data |
| GET | `/dashboard` | Dashboard summary |
| GET | `/report/pdf` | Generate PDF report |
| GET | `/report/excel` | Generate Excel report |

---

## ⚙️ Environment Configuration

### Backend

Create a local `.env` file from `.env.example`:

```env
SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=sqlite:///./budgetbuddy.db
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

The actual `.env` file is intentionally ignored by Git.

### Frontend

Create `client/.env` from `client/.env.example`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

For deployment, this value should point to the deployed HTTPS backend.

---

## 🗃️ Database Migrations

Alembic is configured for schema migrations.

Check the current migration:

```bash
alembic current
```

Apply migrations:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

---

## ▶️ Run Locally

### Backend

From the project root:

```bash
python -m uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Health check:

```text
http://127.0.0.1:8000/health
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```bash
cd client
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

## 🧪 Local Verification

The application has been locally verified for:

- Backend startup and health endpoint
- JWT authentication
- Expense and income operations
- Budget and notification functionality
- Savings goals
- Analytics data flow
- PDF and Excel report generation
- Frontend production build with `npm run build`
- Environment-based frontend API configuration
- User data ownership checks

---

## 🚀 Production Readiness

The codebase includes production-oriented configuration for:

- Environment-based secrets and configuration
- PostgreSQL connection support
- Alembic migrations
- Environment-based CORS
- Environment-based frontend API URL
- Health checking
- Production dependency declaration
- Git-safe environment examples
- Ignoring local databases, virtual environments, build output, and generated reports

Deployment itself is intentionally kept separate from local development verification.

---

## 👨‍💻 Author

**Vatsal Goil**

B.Tech Computer Science — Cyber Security  
Python • React • FastAPI • SQL • Cyber Security

> *Track every rupee. Understand every decision. Grow with every saving.*
