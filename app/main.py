from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import Base, engine, SessionLocal
from .models import User, Expense, Income
from .schemas import (
    UserRegister,
    UserLogin,
    ExpenseCreate,
    IncomeCreate,
    IncomeUpdate,
)
from .auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI App
app = FastAPI(title="BudgetBuddy")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
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
# Dashboard Summary
@app.get("/dashboard")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    recent_income = (
        db.query(Income)
        .filter(Income.user_id == current_user.id)
        .order_by(Income.id.desc())
        .limit(5)
        .all()
    )

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

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "remaining_amount": total_income - total_expense,
        "recent_activity": recent[:5]
    }