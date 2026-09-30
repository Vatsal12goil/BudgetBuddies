from fastapi import FastAPI, Depends, HTTPException  # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]
from sqlalchemy import func  # pyright: ignore[reportMissingImports]
from .models import SavingsGoal
from datetime import date
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
    ExpenseCreate,
    ExpenseUpdate,
    IncomeCreate,
    IncomeUpdate,
    BudgetCreate,
    BudgetUpdate,
)
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
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
    current_month = (expense.date or date.today()).strftime("%Y-%m")

    category_budget = (
        db.query(func.coalesce(func.sum(Budget.amount), 0))
        .filter(
            Budget.user_id == current_user.id,
            Budget.category == expense.category,
            Budget.month == current_month,
        )
        .scalar()
    )

    category_spent = (
        db.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(
            Expense.user_id == current_user.id,
            Expense.category == expense.category,
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
                func.strftime("%Y-%m", Expense.date) == current_month,
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
from datetime import datetime

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
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise HTTPException(400, detail="Invalid month format. Use YYYY-MM")

        query_income = query_income.filter(
            func.strftime("%Y-%m", Income.date) == month
        )
        query_expense = query_expense.filter(
            func.strftime("%Y-%m", Expense.date) == month
        )

    total_income = query_income.with_entities(
        func.coalesce(func.sum(Income.amount), 0)
    ).scalar()

    total_expense = query_expense.with_entities(
        func.coalesce(func.sum(Expense.amount), 0)
    ).scalar()

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
        "category_summary": category_summary,
    }

@app.get("/analytics/trends")
def analytics_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    income_data = (
        db.query(
            func.strftime("%Y-%m", Income.date).label("month"),
            func.sum(Income.amount).label("income"),
        )
        .filter(Income.user_id == current_user.id)
        .group_by("month")
        .all()
    )

    expense_data = (
        db.query(
            func.strftime("%Y-%m", Expense.date).label("month"),
            func.sum(Expense.amount).label("expense"),
        )
        .filter(Expense.user_id == current_user.id)
        .group_by("month")
        .all()
    )

    trends = {}

    for m, amount in income_data:
        trends[m] = {
            "month": m,
            "income": amount,
            "expense": 0,
        }

    for m, amount in expense_data:
        if m not in trends:
            trends[m] = {
                "month": m,
                "income": 0,
                "expense": amount,
            }
        else:
            trends[m]["expense"] = amount

    return sorted(trends.values(), key=lambda x: x["month"])
@app.get("/report/pdf")
def generate_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_name = f"report_{current_user.id}.pdf"

    income = db.query(func.coalesce(func.sum(Income.amount),0)).filter(
        Income.user_id==current_user.id).scalar()

    expense = db.query(func.coalesce(func.sum(Expense.amount),0)).filter(
        Expense.user_id==current_user.id).scalar()
    budget = (
    db.query(func.coalesce(func.sum(Budget.amount), 0))
    .filter(Budget.user_id == current_user.id)
    .scalar()
    )

    goals = db.query(SavingsGoal).filter(
        SavingsGoal.user_id==current_user.id).all()

    pdf = SimpleDocTemplate(file_name)

    data = [
        ["BudgetBuddy Monthly Report",""],
        ["User", current_user.name],
        ["Total Income", f"₹{income}"],
        ["Total Expense", f"₹{expense}"],
        ["Balance", f"₹{budget - expense}"],
        ["",""],
        ["Goal","Saved / Target"]
    ]

    for g in goals:
        data.append([
            g.goal_name,
            f"₹{g.current_saved} / ₹{g.target_amount}"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.grey),
        ("BACKGROUND",(0,0),(-1,0),colors.purple),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
        ("BOTTOMPADDING",(0,0),(-1,0),12),
    ]))

    pdf.build([table])

    return FileResponse(
        file_name,
        filename="BudgetBuddy_Report.pdf",
        media_type="application/pdf"
    )
@app.get("/report/excel")
def generate_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wb = Workbook()
    ws = wb.active
    ws.title = "Budget Report"

    ws.append(["BudgetBuddy Report"])
    ws.append([])

    income = db.query(func.coalesce(func.sum(Income.amount),0)).filter(
        Income.user_id==current_user.id).scalar()

    expense = db.query(func.coalesce(func.sum(Expense.amount),0)).filter(
        Expense.user_id==current_user.id).scalar()
    budget = (
    db.query(func.coalesce(func.sum(Budget.amount), 0))
    .filter(Budget.user_id == current_user.id)
    .scalar()
    )

    ws.append(["Total Income", income])
    ws.append(["Total Expense", expense])
    ws.append(["Balance", budget - expense])
    ws.append([])

    ws.append(["Category","Amount"])

    categories = (
        db.query(
            Expense.category,
            func.sum(Expense.amount)
        )
        .filter(Expense.user_id==current_user.id)
        .group_by(Expense.category)
        .all()
    )

    for c,a in categories:
        ws.append([c,a])

    file_name = f"report_{current_user.id}.xlsx"
    wb.save(file_name)

    return FileResponse(
        file_name,
        filename="BudgetBuddy_Report.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
# =====================================================
# Notifications
# =====================================================

@app.get("/notifications", response_model=list[NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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