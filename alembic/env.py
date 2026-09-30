import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

from app.database import Base
from app.models import (
    User,
    Expense,
    Income,
    Budget,
    SavingsGoal,
    Notification,
)

# Load environment variables from .env
load_dotenv()

config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the database URL from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./budgetbuddy.db"
)

# Tell Alembic about our SQLAlchemy models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        {
            "sqlalchemy.url": DATABASE_URL
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()