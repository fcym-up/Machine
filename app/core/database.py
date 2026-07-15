"""SQLAlchemy database engine and session factory.

Uses SQLite for local development (auto-fallback from PostgreSQL config).
Provides SessionLocal for request-level sessions.
Base is the declarative base class for all ORM models.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Use SQLite for local dev if PostgreSQL is not available
# Try PostgreSQL first; fall back to SQLite if unavailable
raw_url = settings.DATABASE_URL or "sqlite:///./machine.db"
if raw_url.startswith("postgresql"):
    try:
        from sqlalchemy import exc
        test_engine = create_engine(raw_url)
        test_engine.connect().close()
        engine = create_engine(raw_url, echo=False)
    except exc.OperationalError:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "machine.db")
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, echo=False)
        print("PostgreSQL unavailable, falling back to SQLite")
else:
    engine = create_engine(raw_url, connect_args={"check_same_thread": False}, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
