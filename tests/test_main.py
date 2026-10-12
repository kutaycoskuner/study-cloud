# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-12
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
Tests for app/main.py through FastAPI's TestClient (no server needed).

Run: python -m pytest   (from the repo root, so `app` is importable)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app, notes

client = TestClient(app)


@pytest.fixture(autouse=True)
def empty_store():
    """Each test starts with no notes, so tests don't depend on each other's order."""
    notes.clear()


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
