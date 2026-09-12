from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional


# ---------- USER ----------

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ---------- EXPENSE ----------

class ExpenseCreate(BaseModel):
    title: str
    amount: float


# ---------- INCOME ----------

class IncomeCreate(BaseModel):
    amount: float
    source: str
    date: date
    description: Optional[str] = None


class IncomeUpdate(BaseModel):
    amount: float
    source: str
    date: date
    description: Optional[str] = None


class IncomeResponse(BaseModel):
    id: int
    amount: float
    source: str
    date: date
    description: Optional[str]

    class Config:
        from_attributes = True