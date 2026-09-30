import os
from importlib import import_module

try:
    _sqlalchemy = import_module("sqlalchemy")
    _sqlalchemy_orm = import_module("sqlalchemy.orm")

    create_engine = _sqlalchemy.create_engine
    declarative_base = _sqlalchemy_orm.declarative_base
    sessionmaker = _sqlalchemy_orm.sessionmaker

except ImportError as exc:
    raise RuntimeError(
        "SQLAlchemy is required. Install it with: python -m pip install sqlalchemy"
    ) from exc


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./budgetbuddy.db"
)

# Render/PostgreSQL may provide postgres:// or postgresql://
# psycopg3 uses the postgresql+psycopg:// driver.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )


if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()