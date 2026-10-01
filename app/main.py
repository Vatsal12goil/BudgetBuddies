from fastapi import FastAPI, Depends, HTTPException  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]
from sqlalchemy import func  # pyright: ignore[reportMissingImports]
from .models import SavingsGoal
from datetime import date, datetime, timedelta
from fastapi.responses import FileResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from openpyxl import Workbook
import os
from dotenv import load_dotenv
from app.models import Notification
from app.schemas import NotificationOut
from .schemas import (
    SavingsGoalCreate,
    SavingsGoalUpdate,
    SavingsProgressUpdate,
)

from .database import Base, engine, SessionLocal
from .models import User, Expense, Income, Budget
from .schemas import (
    UserRegister,
    UserLogin,
    UserProfileUpdate,
    ExpenseCreate,
    ExpenseUpdate,
    IncomeCreate,
    IncomeUpdate,
    BudgetCreate,
    BudgetUpdate,
    RoleUpdate,
)
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
)
load_dotenv()
# Create tables

# FastAPI App
app = FastAPI(title="BudgetBuddy")

# CORS
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


def month_bounds(month: str):
    try:
        parsed = datetime.strptime(month, "%Y-%m")
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid month format. Use YYYY-MM",
        ) from exc

    start = parsed.date().replace(day=1)
    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)

    return start, end

# Home
@app.get("/")
def home():
    return {"message": "BudgetBuddy Running"}


# Register
@app.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role="student",
    )

    db.add(new_user)
    db.commit()

    return {"message": "Registered Successfully"}


# Login
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Wrong Password")

    token = create_access_token(db_user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": db_user.role,
    }


# Current User
@app.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }


# User Profile Management
@app.get("/profile")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "monthly_income": current_user.monthly_income,
        "financial_preference": current_user.financial_preference,
        "account_setting": current_user.account_setting,
    }


@app.put("/profile")
def update_profile(
    profile: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not profile.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    if profile.monthly_income is not None and profile.monthly_income < 0:
        raise HTTPException(status_code=400, detail="Monthly income cannot be negative")

    current_user.name = profile.name.strip()
    current_user.monthly_income = profile.monthly_income
    current_user.financial_preference = profile.financial_preference
    current_user.account_setting = profile.account_setting

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile Updated Successfully",
        "profile": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "monthly_income": current_user.monthly_income,
            "financial_preference": current_user.financial_preference,
            "account_setting": current_user.account_setting,
        },
    }


# Add Expense
@app.post("/expenses")
def add_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_categories = [
        "Food",
        "Travel",
        "Shopping",
        "Education",
        "Entertainment",
        "Miscellaneous",
    ]

    if expense.category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category")
    # ==========================
    # Budget Limit Validation
    # ==========================
    total_budget = (
        db.query(func.coalesce(func.sum(Budget.amount), 0))
        .filter(Budget.user_id == current_user.id)
        .scalar()
    )

    total_income = (
        db.query(func.coalesce(func.sum(Income.amount), 0))
        .filter(Income.user_id == current_user.id)
        .scalar()
    )

    total_expense = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.user_id == current_user.id)
        .scalar()
    )

    available = total_budget + total_income - total_expense

    if expense.amount > available:
        raise HTTPException(
            status_code=400,
            detail=f"Budget limit reached! Only ₹{available} remaining.",
        )

    # ===== Category Budget Validation =====#
    expense_date = expense.date or date.today()
    current_month = expense_date.strftime("%Y-%m")

    category_budget = (
        db.query(func.coalesce(func.sum(Budget.amount), 0))
        .filter(
            Budget.user_id == current_user.id,
            Budget.category == expense.category,
            Budget.month == current_month,
        )
        .scalar()
    )

    month_start = expense_date.replace(day=1)
    if month_start.month == 12:
        next_month_start = date(month_start.year + 1, 1, 1)
    else:
        next_month_start = date(month_start.year, month_start.month + 1, 1)

    category_spent = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.user_id == current_user.id,
            Expense.category == expense.category,
            Expense.date >= month_start,
            Expense.date < next_month_start,
        )
        .scalar()
    )

    if category_budget == 0:
        raise HTTPException(
            status_code=400,
            detail=f"No budget set for {expense.category}",
        )

    if category_spent + expense.amount > category_budget:
        remaining = max(0, category_budget - category_spent)
        raise HTTPException(
            status_code=400,
            detail=f"{expense.category} budget exceeded! Only ₹{remaining} left.",
        )
    # ===== Budget Notification Trigger =====

    new_total = category_spent + expense.amount
    percent = (new_total / category_budget) * 100

    # Duplicate notification avoid
    last_notification = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.type == "budget",
            Notification.related_id == hash(expense.category),
        )
        .order_by(Notification.created_at.desc())
        .first()
    )

    if percent >= 100:
        message = f"{expense.category} budget exceeded!"
    elif percent >= 80:
        message = f"{expense.category} budget reached {int(percent)}%"
    else:
        message = None

    if message and (
        not last_notification or last_notification.message != message
    ):
        db.add(
            Notification(
                user_id=current_user.id,
                type="budget",
                message=message,
                related_id=hash(expense.category),
            )
        )
    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        date=expense.date or date.today(),
        user_id=current_user.id,
    )

    db.add(new_expense)
    db.commit()

    return {"message": "Expense Added"}
# My Expenses
@app.get("/expenses")
def my_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).all()
# Update Expense
@app.put("/expenses/{expense_id}")
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_categories = [
        "Food",
        "Travel",
        "Shopping",
        "Education",
        "Entertainment",
        "Miscellaneous",
    ]

    if expense.category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category")

    record = (
        db.query(Expense)
        .filter(
            Expense.id == expense_id,
            Expense.user_id == current_user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Expense not found")

    record.title = expense.title
    record.amount = expense.amount
    record.category = expense.category

    db.commit()

    return {"message": "Expense Updated"}
# Delete Expense
@app.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(Expense)
        .filter(
            Expense.id == expense_id,
            Expense.user_id == current_user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(record)
    db.commit()

    return {"message": "Expense Deleted"}
# Add Income
@app.post("/income")
def add_income(
    income: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_sources = [
        "Pocket Money",
        "Scholarship",
        "Freelance Income",
    ]

    if income.source not in valid_sources:
        raise HTTPException(status_code=400, detail="Invalid income source")

    new_income = Income(
        amount=income.amount,
        source=income.source,
        date=income.date,
        description=income.description,
        user_id=current_user.id,
    )

    db.add(new_income)
    db.commit()

    return {"message": "Income Added"}
# My Income
@app.get("/income")
def my_income(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Income)
        .filter(Income.user_id == current_user.id)
        .all()
    )


# Update Income
@app.put("/income/{income_id}")
def update_income(
    income_id: int,
    income: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(Income)
        .filter(
            Income.id == income_id,
            Income.user_id == current_user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Income not found")

    record.amount = income.amount
    record.source = income.source
    record.date = income.date
    record.description = income.description

    db.commit()

    return {"message": "Income Updated"}


# Delete Income
@app.delete("/income/{income_id}")
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(Income)
        .filter(
            Income.id == income_id,
            Income.user_id == current_user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Income not found")

    db.delete(record)
    db.commit()

    return {"message": "Income Deleted"}

    # =====================================================
# Dashboard Summary
# Returns totals and recent financial activity
# =====================================================
@app.get("/dashboard")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_month = date.today().strftime("%Y-%m")

    # Total Income
    total_income = (
        db.query(func.coalesce(func.sum(Income.amount), 0))
        .filter(Income.user_id == current_user.id)
        .scalar()
    )

    # Total Expense
    total_expense = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.user_id == current_user.id)
        .scalar()
    )

    # Total Budget
    total_budget = (
        db.query(func.coalesce(func.sum(Budget.amount), 0))
        .filter(Budget.user_id == current_user.id)
        .scalar()
    )

    # Last 5 incomes
    recent_income = (
        db.query(Income)
        .filter(Income.user_id == current_user.id)
        .order_by(Income.id.desc())
        .limit(5)
        .all()
    )

    # Last 5 expenses
    recent_expense = (
        db.query(Expense)
        .filter(Expense.user_id == current_user.id)
        .order_by(Expense.id.desc())
        .limit(5)
        .all()
    )

    recent = []

    for i in recent_income:
        recent.append({
            "type": "Income",
            "title": i.source,
            "amount": i.amount,
            "date": str(i.date)
        })

    for e in recent_expense:
        recent.append({
            "type": "Expense",
            "title": e.title,
            "amount": e.amount,
            "date": "-"
        })

    recent.sort(key=lambda x: x["date"], reverse=True)
    # Category wise budget + spent
    current_month = date.today().strftime("%Y-%m")
    month_start = date.today().replace(day=1)
    if month_start.month == 12:
        next_month_start = date(month_start.year + 1, 1, 1)
    else:
        next_month_start = date(month_start.year, month_start.month + 1, 1)
    category_summary = []

    categories = [
        "Food","Travel","Shopping",
        "Education","Entertainment","Miscellaneous"
    ]

    for cat in categories:
        budget = (
            db.query(func.coalesce(func.sum(Budget.amount), 0))
            .filter(
                Budget.user_id == current_user.id,
                Budget.category == cat,
                Budget.month == current_month,
            )
            .scalar()
        )

        spent = (
            db.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(
                Expense.user_id == current_user.id,
                Expense.category == cat,
                Expense.date >= month_start,
                Expense.date < next_month_start,
            )
            .scalar()
        )

        category_summary.append({
            "category": cat,
            "budget": budget,
            "spent": min(spent, budget),   # UI me budget se upar nahi dikhayega
            "actual_spent": spent,         # Original value preserve rahegi
        })

    # Available Budget
    remaining_amount = max(0, total_budget - total_expense)

    return {
    "total_income": total_income,
    "total_expense": total_expense,
    "total_budget": total_budget,

    # ✅ sahi
    "remaining_amount": remaining_amount,

    "recent_activity": recent[:5],
    "category_summary": category_summary,
}
# =====================================================
# Create / Update Budget
# One budget per category per month
# =====================================================
@app.post("/budget")
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valid_categories = [
        "Food",
        "Travel",
        "Shopping",
        "Education",
        "Entertainment",
        "Miscellaneous",
    ]

    if budget.category not in valid_categories:
        raise HTTPException(status_code=400, detail="Invalid category")

    if budget.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid budget amount")

    # Check existing category budget
    existing = (
        db.query(Budget)
        .filter(
            Budget.user_id == current_user.id,
            Budget.category == budget.category,
            Budget.month == budget.month,
        )
        .first()
    )

    if existing:
        existing.amount = budget.amount
        db.commit()
        return {"message": "Budget Updated"}

    new_budget = Budget(
        category=budget.category,
        amount=budget.amount,
        month=budget.month,
        user_id=current_user.id,
    )

    db.add(new_budget)
    db.commit()

    return {"message": "Budget Created"}

# View Budgets
@app.get("/budget")
def get_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id)
        .all()
    )
# ==========================
# Update Budget
# ==========================
@app.put("/budget/{budget_id}")
def update_budget(
    budget_id: int,
    budget: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(Budget)
        .filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Budget not found")

    record.category = budget.category
    record.amount = budget.amount
    record.month = budget.month

    db.commit()

    return {"message": "Budget Updated"}

# Reset All Budgets
@app.delete("/budget/reset")
def reset_budget(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Budget).filter(
        Budget.user_id == current_user.id
    ).delete()

    db.commit()

    return {"message": "All budgets reset successfully"}
# ==========================
# Delete Budget
# ==========================
@app.delete("/budget/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = (
        db.query(Budget)
        .filter(
            Budget.id == budget_id,
            Budget.user_id == current_user.id,
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(record)
    db.commit()

    return {"message": "Budget Deleted"}

@app.post("/goals")
def create_goal(
    goal: SavingsGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if goal.goal_name.strip() == "":
        raise HTTPException(400, "Goal name required")

    if goal.target_amount <= 0:
        raise HTTPException(400, "Target amount must be greater than 0")

    new_goal = SavingsGoal(
        goal_name=goal.goal_name,
        target_amount=goal.target_amount,
        current_saved=0,
        user_id=current_user.id,
    )

    db.add(new_goal)
    db.commit()

    return {"message": "Goal Created"}

@app.get("/goals")
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(SavingsGoal).filter(
        SavingsGoal.user_id == current_user.id
    ).all()
@app.put("/goals/{goal_id}")
def update_goal(
    goal_id: int,
    goal: SavingsGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(404, detail="Goal not found")

    if goal.target_amount <= 0:
        raise HTTPException(400, detail="Invalid target amount")

    record.goal_name = goal.goal_name
    record.target_amount = goal.target_amount

    db.commit()

    return {"message": "Goal Updated"}
@app.patch("/goals/{goal_id}/progress")
def update_progress(
    goal_id: int,
    progress: SavingsProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(404, detail="Goal not found")

    if progress.current_saved < 0:
        raise HTTPException(400, detail="Invalid amount")

    record.current_saved = min(
        record.current_saved + progress.current_saved,
        record.target_amount
    )

    record.is_completed = (
        record.current_saved >= record.target_amount
    )

    # ===== Savings Milestone Notification =====
    progress_percent = (
        record.current_saved / record.target_amount
    ) * 100

    if progress_percent >= 50 and not record.is_completed:
        exists = (
            db.query(Notification)
            .filter(
                Notification.user_id == current_user.id,
                Notification.type == "savings_milestone",
                Notification.related_id == record.id,
            )
            .first()
        )

        if not exists:
            db.add(
                Notification(
                    user_id=current_user.id,
                    type="savings_milestone",
                    message=f"🎯 50% milestone reached for: {record.goal_name}",
                    related_id=record.id,
                )
            )

    # ===== Savings Notification Trigger =====
    if record.is_completed:
        exists = (
            db.query(Notification)
            .filter(
                Notification.user_id == current_user.id,
                Notification.type == "savings",
                Notification.related_id == record.id,
            )
            .first()
        )

        if not exists:
            db.add(
                Notification(
                    user_id=current_user.id,
                    type="savings",
                    message=f"🎉 Goal completed: {record.goal_name}",
                    related_id=record.id,
                )
            )

    db.commit()

    return {
        "message": "Progress Updated",
        "progress": round(
            (record.current_saved / record.target_amount) * 100,
            2,
        ),
        "completed": record.is_completed,
    }
@app.delete("/goals/{goal_id}")
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(404, detail="Goal not found")

    db.delete(record)
    db.commit()

    return {"message": "Goal Deleted"}
@app.get("/analytics")
def get_analytics(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query_income = db.query(Income).filter(Income.user_id == current_user.id)
    query_expense = db.query(Expense).filter(Expense.user_id == current_user.id)

    # Month filter (YYYY-MM)
    if month:
        month_start, next_month_start = month_bounds(month)
        query_income = query_income.filter(
            Income.date >= month_start,
            Income.date < next_month_start,
        )
        query_expense = query_expense.filter(
            Expense.date >= month_start,
            Expense.date < next_month_start,
        )

    total_income = query_income.with_entities(
        func.coalesce(func.sum(Income.amount), 0)
    ).scalar()

    total_expense = query_expense.with_entities(
        func.coalesce(func.sum(Expense.amount), 0)
    ).scalar()

    # Savings summary
    total_saved = (
        db.query(func.coalesce(func.sum(SavingsGoal.current_saved), 0))
        .filter(SavingsGoal.user_id == current_user.id)
        .scalar()
    )

    total_target = (
        db.query(func.coalesce(func.sum(SavingsGoal.target_amount), 0))
        .filter(SavingsGoal.user_id == current_user.id)
        .scalar()
    )

    # Category summary
    category_data = (
        query_expense.with_entities(
            Expense.category,
            func.sum(Expense.amount)
        )
        .group_by(Expense.category)
        .all()
    )

    category_summary = [
        {"category": c, "amount": a}
        for c, a in category_data
    ]

    return {
        "month": month,
        "summary": {
            "income": total_income,
            "expense": total_expense,
            "balance": total_income - total_expense,
        },
        "savings": {
            "total_saved": total_saved,
            "total_target": total_target,
        },
        "category_summary": category_summary,
    }

@app.get("/analytics/trends")
def analytics_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incomes = (
        db.query(Income)
        .filter(Income.user_id == current_user.id)
        .all()
    )
    expenses = (
        db.query(Expense)
        .filter(Expense.user_id == current_user.id)
        .all()
    )

    trends = {}

    for item in incomes:
        month_key = item.date.strftime("%Y-%m")
        trends.setdefault(
            month_key,
            {"month": month_key, "income": 0, "expense": 0},
        )
        trends[month_key]["income"] += item.amount

    for item in expenses:
        month_key = item.date.strftime("%Y-%m")
        trends.setdefault(
            month_key,
            {"month": month_key, "income": 0, "expense": 0},
        )
        trends[month_key]["expense"] += item.amount

    return sorted(trends.values(), key=lambda x: x["month"])


@app.get("/report/pdf")
def generate_pdf(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    income_query = db.query(Income).filter(Income.user_id == current_user.id)
    expense_query = db.query(Expense).filter(Expense.user_id == current_user.id)

    if month:
        month_start, next_month_start = month_bounds(month)
        income_query = income_query.filter(
            Income.date >= month_start,
            Income.date < next_month_start,
        )
        expense_query = expense_query.filter(
            Expense.date >= month_start,
            Expense.date < next_month_start,
        )

    income = income_query.with_entities(
        func.coalesce(func.sum(Income.amount), 0)
    ).scalar()
    expense = expense_query.with_entities(
        func.coalesce(func.sum(Expense.amount), 0)
    ).scalar()

    expenses = expense_query.order_by(Expense.date.desc()).all()
    goals = db.query(SavingsGoal).filter(
        SavingsGoal.user_id == current_user.id
    ).all()

    report_title = (
        f"BudgetBuddy Monthly Report - {month}"
        if month
        else "BudgetBuddy Financial Report"
    )

    file_name = f"report_{current_user.id}.pdf"
    pdf = SimpleDocTemplate(file_name)

    data = [
        [report_title, "", "", ""],
        ["User", current_user.name, "", ""],
        ["Total Income", f"₹{income}", "", ""],
        ["Total Expense", f"₹{expense}", "", ""],
        ["Balance", f"₹{income - expense}", "", ""],
        ["", "", "", ""],
        ["Expense History", "", "", ""],
        ["Title", "Category", "Amount", "Date"],
    ]

    for e in expenses:
        data.append([e.title, e.category, f"₹{e.amount}", str(e.date)])

    data.extend([
        ["", "", "", ""],
        ["Savings Goals", "", "", ""],
        ["Goal", "Saved", "Target", "Status"],
    ])

    for g in goals:
        data.append([
            g.goal_name,
            f"₹{g.current_saved}",
            f"₹{g.target_amount}",
            "Completed" if g.is_completed else "In Progress",
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.purple),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
    ]))

    pdf.build([table])

    return FileResponse(
        file_name,
        filename="BudgetBuddy_Report.pdf",
        media_type="application/pdf",
    )


@app.get("/report/excel")
def generate_excel(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    income_query = db.query(Income).filter(Income.user_id == current_user.id)
    expense_query = db.query(Expense).filter(Expense.user_id == current_user.id)

    if month:
        month_start, next_month_start = month_bounds(month)
        income_query = income_query.filter(
            Income.date >= month_start,
            Income.date < next_month_start,
        )
        expense_query = expense_query.filter(
            Expense.date >= month_start,
            Expense.date < next_month_start,
        )

    income = income_query.with_entities(
        func.coalesce(func.sum(Income.amount), 0)
    ).scalar()
    expense = expense_query.with_entities(
        func.coalesce(func.sum(Expense.amount), 0)
    ).scalar()
    expenses = expense_query.order_by(Expense.date.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Budget Report"

    ws.append([
        f"BudgetBuddy Monthly Report - {month}"
        if month
        else "BudgetBuddy Financial Report"
    ])
    ws.append([])
    ws.append(["User", current_user.name])
    ws.append(["Total Income", income])
    ws.append(["Total Expense", expense])
    ws.append(["Balance", income - expense])
    ws.append([])
    ws.append(["Expense History"])
    ws.append(["Title", "Category", "Amount", "Date"])

    for e in expenses:
        ws.append([e.title, e.category, e.amount, str(e.date)])

    ws.append([])
    ws.append(["Category Summary"])
    ws.append(["Category", "Amount"])

    categories = (
        expense_query
        .with_entities(Expense.category, func.sum(Expense.amount))
        .group_by(Expense.category)
        .all()
    )

    for category, amount in categories:
        ws.append([category, amount])

    file_name = f"report_{current_user.id}.xlsx"
    wb.save(file_name)

    return FileResponse(
        file_name,
        filename="BudgetBuddy_Report.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# =====================================================
# Scheduled Notifications
# =====================================================

def generate_scheduled_notifications(
    db: Session,
    current_user: User,
):
    now = datetime.utcnow()

    # Savings reminder: first reminder immediately, then once every 7 days.
    goals = (
        db.query(SavingsGoal)
        .filter(
            SavingsGoal.user_id == current_user.id,
            SavingsGoal.is_completed == False,
        )
        .all()
    )

    for goal in goals:
        last_reminder = (
            db.query(Notification)
            .filter(
                Notification.user_id == current_user.id,
                Notification.type == "savings_reminder",
                Notification.related_id == goal.id,
            )
            .order_by(Notification.created_at.desc())
            .first()
        )

        if (
            not last_reminder
            or not last_reminder.created_at
            or now - last_reminder.created_at >= timedelta(days=7)
        ):
            db.add(
                Notification(
                    user_id=current_user.id,
                    type="savings_reminder",
                    message=f"💰 Keep saving for your goal: {goal.goal_name}",
                    related_id=goal.id,
                )
            )

    # Monthly report notification during the first 7 days of a new month.
    if now.day <= 7:
        previous_month = (
            (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        )

        existing = (
            db.query(Notification)
            .filter(
                Notification.user_id == current_user.id,
                Notification.type == "monthly_report",
                Notification.message.contains(previous_month),
            )
            .first()
        )

        if not existing:
            db.add(
                Notification(
                    user_id=current_user.id,
                    type="monthly_report",
                    message=(
                        f"📊 Your BudgetBuddy monthly report for "
                        f"{previous_month} is ready."
                    ),
                )
            )

    db.commit()


# =====================================================
# Notifications
# =====================================================

@app.get("/notifications", response_model=list[NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    generate_scheduled_notifications(db, current_user)

    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@app.get("/notifications/unread", response_model=list[NotificationOut])
def get_unread_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .order_by(Notification.created_at.desc())
        .all()
    )

@app.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)   # ← ye line add karo

    return notification

@app.get("/admin-test")
def admin_test(
    current_user: User = Depends(require_role("admin")),
):
    return {
        "message": "Admin access granted",
        "user": current_user.email,
        "role": current_user.role,
    }


@app.patch("/admin/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role_update.role
    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "role": user.role,
        "updated_by": current_admin.email,
    }
