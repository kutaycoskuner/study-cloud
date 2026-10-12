# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-13
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Database connection and the notes table.

DATABASE_URL picks the database: PostgreSQL in Docker Compose (set in
docker-compose.yaml), a local SQLite file otherwise, so the app runs without Docker.

Requires: sqlalchemy; psycopg for postgresql+psycopg:// URLs.
"""

import os
from collections.abc import Iterator

from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")

# SQLite refuses connections shared across threads by default; FastAPI runs each request
# in a worker thread, so allow it (PostgreSQL needs no such option)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Parent of all table classes; collects their definitions in Base.metadata."""


class NoteRow(Base):
    """The notes table: one row per note."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(1000))


def create_tables() -> None:
    """Creates missing tables; existing tables and their data are left alone."""
    Base.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one session per request, closed afterwards."""
    with SessionLocal() as session:
        yield session
