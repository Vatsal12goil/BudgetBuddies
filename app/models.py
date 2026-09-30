from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import date, datetime
from sqlalchemy import DateTime, Boolean
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="student")
    monthly_income = Column(Float, nullable=True)
    financial_preference = Column(String, nullable=True)
    account_setting = Column(String, nullable=True)
    monthly_income = Column(Float, nullable=True)
    financial_preference = Column(String, nullable=True)
    account_setting = Column(String, nullable=True)

    expenses = relationship("Expense", back_populates="user")
    incomes = relationship("Income", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    notifications = relationship("Notification", back_populates="owner")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    date = Column(Date, default=date.today)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="expenses")


class Income(Base):
    __tablename__ = "income"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    date = Column(Date, default=date.today)
    description = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="incomes")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="budgets")



class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, index=True)
    goal_name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_saved = Column(Float, default=0)

    is_completed = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"))
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    type = Column(String)           # budget | savings
    message = Column(String)

    is_read = Column(Boolean, default=False)

    related_id = Column(Integer, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    owner = relationship("User", back_populates="notifications")