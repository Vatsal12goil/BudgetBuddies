import os
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app import auth
from app.main import app
import app.main as main_module


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[main_module.get_db] = override_db
    app.dependency_overrides[auth.get_db] = override_db

    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        with TestClient(app) as test_client:
            yield test_client, TestingSessionLocal
    finally:
        os.chdir(old_cwd)
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def register_and_login(client, email, name="Test User"):
    response = client.post(
        "/register",
        json={"name": name, "email": email, "password": "Pass123!"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        "/login",
        json={"email": email, "password": "Pass123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_full_financial_workflow(client):
    client, _ = client
    token = register_and_login(client, "flow@example.com", "Flow User")
    headers = auth_headers(token)

    # Login -> Add Income
    response = client.post(
        "/income",
        headers=headers,
        json={
            "amount": 10000,
            "source": "Pocket Money",
            "date": str(date.today()),
            "description": "Monthly income",
        },
    )
    assert response.status_code == 200, response.text

    # Create Budget -> Assign category through expense
    response = client.post(
        "/budget",
        headers=headers,
        json={
            "category": "Food",
            "amount": 1000,
            "month": date.today().strftime("%Y-%m"),
        },
    )
    assert response.status_code == 200, response.text

    # Add Expense and cross 80% budget threshold
    response = client.post(
        "/expenses",
        headers=headers,
        json={
            "title": "Groceries",
            "amount": 850,
            "category": "Food",
            "date": str(date.today()),
        },
    )
    assert response.status_code == 200, response.text

    notifications = client.get("/notifications", headers=headers)
    assert notifications.status_code == 200, notifications.text
    assert any(
        n["type"] == "budget" and "80%" in n["message"]
        for n in notifications.json()
    )

    # Create Savings Goal -> Update Savings Progress
    response = client.post(
        "/goals",
        headers=headers,
        json={"goal_name": "Emergency Fund", "target_amount": 1000},
    )
    assert response.status_code == 200, response.text

    goals = client.get("/goals", headers=headers)
    assert goals.status_code == 200
    goal_id = goals.json()[0]["id"]

    response = client.patch(
        f"/goals/{goal_id}/progress",
        headers=headers,
        json={"current_saved": 500},
    )
    assert response.status_code == 200, response.text
    assert response.json()["progress"] == 50.0

    # Analytics
    response = client.get(
        f"/analytics?month={date.today().strftime('%Y-%m')}",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    analytics = response.json()
    assert analytics["summary"]["income"] == 10000
    assert analytics["summary"]["expense"] == 850
    assert analytics["savings"]["total_saved"] == 500

    # Dashboard consistency
    response = client.get("/dashboard", headers=headers)
    assert response.status_code == 200, response.text
    dashboard = response.json()
    assert dashboard["total_income"] == 10000
    assert dashboard["total_expense"] == 850
    assert dashboard["total_budget"] == 1000
    assert dashboard["remaining_amount"] == 150

    # Reports
    month = date.today().strftime("%Y-%m")
    response = client.get(f"/report/pdf?month={month}", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")

    response = client.get(f"/report/excel?month={month}", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_negative_inputs_and_authorization(client):
    client, _ = client
    token1 = register_and_login(client, "user1@example.com", "User One")
    token2 = register_and_login(client, "user2@example.com", "User Two")
    h1 = auth_headers(token1)
    h2 = auth_headers(token2)

    # Unauthorized request
    assert client.get("/dashboard").status_code in {401, 403}

    # Missing required fields
    assert client.post("/register", json={"email": "missing@example.com"}).status_code == 422

    # Invalid amounts
    assert client.post(
        "/income",
        headers=h1,
        json={
            "amount": -100,
            "source": "Pocket Money",
            "date": str(date.today()),
        },
    ).status_code == 422

    assert client.post(
        "/expenses",
        headers=h1,
        json={
            "title": "Invalid",
            "amount": -10,
            "category": "Food",
        },
    ).status_code == 422

    # Invalid category/source
    assert client.post(
        "/budget",
        headers=h1,
        json={"category": "Invalid", "amount": 100, "month": date.today().strftime("%Y-%m")},
    ).status_code == 400

    assert client.post(
        "/income",
        headers=h1,
        json={
            "amount": 100,
            "source": "Invalid Source",
            "date": str(date.today()),
        },
    ).status_code == 400

    # Invalid IDs
    assert client.get("/expenses/999999", headers=h1).status_code in {404, 405}
    assert client.delete("/expenses/999999", headers=h1).status_code == 404
    assert client.delete("/notifications/999999/read", headers=h1).status_code == 404

    # Empty-data situation for second user
    assert client.get("/expenses", headers=h2).json() == []
    assert client.get("/income", headers=h2).json() == []
    assert client.get("/budget", headers=h2).json() == []
    assert client.get("/goals", headers=h2).json() == []
    assert client.get("/notifications/unread", headers=h2).json() == []

    analytics = client.get("/analytics", headers=h2)
    assert analytics.status_code == 200
    assert analytics.json()["summary"]["income"] == 0
    assert analytics.json()["summary"]["expense"] == 0

    # Create user1 data, then ensure user2 cannot access it.
    assert client.post(
        "/income",
        headers=h1,
        json={
            "amount": 500,
            "source": "Pocket Money",
            "date": str(date.today()),
        },
    ).status_code == 200

    assert client.post(
        "/budget",
        headers=h1,
        json={
            "category": "Food",
            "amount": 1000,
            "month": date.today().strftime("%Y-%m"),
        },
    ).status_code == 200

    assert client.post(
        "/expenses",
        headers=h1,
        json={
            "title": "Private expense",
            "amount": 100,
            "category": "Food",
            "date": str(date.today()),
        },
    ).status_code == 200

    expense_id = client.get("/expenses", headers=h1).json()[0]["id"]
    assert client.delete(f"/expenses/{expense_id}", headers=h2).status_code == 404
    assert client.get("/expenses", headers=h2).json() == []


def test_admin_role_protection_and_role_update(client):
    client, Session = client
    token1 = register_and_login(client, "admin@example.com", "Admin User")
    token2 = register_and_login(client, "member@example.com", "Member User")

    db = Session()
    try:
        admin = db.query(main_module.User).filter(main_module.User.email == "admin@example.com").first()
        admin.role = "admin"
        db.commit()
    finally:
        db.close()

    admin_headers = auth_headers(token1)
    member_headers = auth_headers(token2)

    assert client.get("/admin-test", headers=member_headers).status_code == 403
    assert client.get("/admin-test", headers=admin_headers).status_code == 200

    member = client.get("/me", headers=member_headers).json()
    response = client.patch(
        f"/admin/users/{member['id']}/role",
        headers=admin_headers,
        json={"role": "premium"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "premium"
