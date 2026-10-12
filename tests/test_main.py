# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-13
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Tests for app/main.py through FastAPI's TestClient (no server needed).

Each test runs against its own empty SQLite file, swapped in for the real database
through FastAPI's dependency_overrides, so no Docker or PostgreSQL is needed.

Run: python -m pytest   (from the repo root, so `app` is importable)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_session
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def test_db(tmp_path):
    """Each test gets its own empty SQLite file, so tests never touch real data."""
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    def session_override():
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = session_override
    yield
    app.dependency_overrides.clear()
    engine.dispose()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get_note():
    created = client.post("/notes", json={"text": "hello"})
    assert created.status_code == 201
    note = created.json()
    assert note == {"id": 1, "text": "hello"}
    assert client.get(f"/notes/{note['id']}").json() == note
    assert client.get("/notes").json() == [note]


def test_missing_note_is_404():
    assert client.get("/notes/99").status_code == 404
