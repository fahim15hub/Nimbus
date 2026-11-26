"""
db.py  -  database setup using SQLite (one file, no server needed)
and SQLAlchemy (a library that lets us use Python classes as tables).
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

import os
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def utcnow() -> datetime:
    """Current time in UTC, stored without timezone info (SQLite has no timezones)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    light: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    presence: Mapped[bool] = mapped_column(Boolean, default=False)
    distance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    type: Mapped[str] = mapped_column(String(20))      # exam, class, deadline, reminder
    due_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False)


def get_db():
    """FastAPI 'dependency': gives each request its own DB session, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
