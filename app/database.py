try:
    from importlib import import_module

    _sqlalchemy = import_module("sqlalchemy")
    _sqlalchemy_orm = import_module("sqlalchemy.orm")
    create_engine = _sqlalchemy.create_engine
    declarative_base = _sqlalchemy_orm.declarative_base
    sessionmaker = _sqlalchemy_orm.sessionmaker
except ImportError as exc:
    raise RuntimeError(
        "SQLAlchemy is required. Install it with: python -m pip install sqlalchemy"
    ) from exc

DATABASE_URL = "sqlite:///./budgetbuddy.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE expenses ADD COLUMN date DATE"))
        conn.commit()
        print("Expense date column added")
    except:
        pass

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()