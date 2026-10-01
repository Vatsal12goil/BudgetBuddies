from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import date as date_type, datetime
from typing import Literal, Optional


# ---------- USER ----------

class UserRegister(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=1)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    name: str = Field(min_length=1)
    monthly_income: Optional[float] = Field(default=None, ge=0)
    financial_preference: Optional[str] = None
    account_setting: Optional[str] = None


# ---------- EXPENSE ----------

class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1)
    date: date_type | None = None

class ExpenseUpdate(BaseModel):
    title: str = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1)

# ---------- INCOME ----------

class IncomeCreate(BaseModel):
    amount: float = Field(gt=0)
    source: str = Field(min_length=1)
    date: date_type
    description: Optional[str] = None


class IncomeUpdate(BaseModel):
    amount: float = Field(gt=0)
    source: str = Field(min_length=1)
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
    category: str = Field(min_length=1)
    amount: float = Field(gt=0)
    month: str = Field(pattern=r"^\d{4}-\d{2}$")


class BudgetUpdate(BaseModel):
    category: str = Field(min_length=1)
    amount: float = Field(gt=0)
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
class SavingsGoalCreate(BaseModel):
    goal_name: str = Field(min_length=1)
    target_amount: float = Field(gt=0)


class SavingsGoalUpdate(BaseModel):
    goal_name: str = Field(min_length=1)
    target_amount: float = Field(gt=0)


class SavingsProgressUpdate(BaseModel):
    current_saved: float = Field(ge=0)
class NotificationOut(BaseModel):
    id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationRead(BaseModel):
    is_read: bool

class RoleUpdate(BaseModel):
    role: Literal["student", "premium", "admin"]
