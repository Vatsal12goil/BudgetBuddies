from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import date as date_type, datetime
from typing import Optional


# ---------- USER ----------

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    name: str
    monthly_income: Optional[float] = None
    financial_preference: Optional[str] = None
    account_setting: Optional[str] = None


# ---------- EXPENSE ----------

class ExpenseCreate(BaseModel):
    title: str
    amount: int
    category: str
    date: date_type | None = None

class ExpenseUpdate(BaseModel):
    title: str
    amount: float
    category: str

# ---------- INCOME ----------

class IncomeCreate(BaseModel):
    amount: float
    source: str
    date: date_type
    description: Optional[str] = None


class IncomeUpdate(BaseModel):
    amount: float
    source: str
    date: date_type
    description: Optional[str] = None


class IncomeResponse(BaseModel):
    id: int
    amount: float
    source: str
    date: date_type
    description: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ---------- BUDGET ----------

class BudgetCreate(BaseModel):
    category: str
    amount: float
    month: str


class BudgetUpdate(BaseModel):
    category: str
    amount: float
    month: str
class SavingsGoalCreate(BaseModel):
    goal_name: str
    target_amount: float


class SavingsGoalUpdate(BaseModel):
    goal_name: str
    target_amount: float


class SavingsProgressUpdate(BaseModel):
    current_saved: float
class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationRead(BaseModel):
    is_read: bool