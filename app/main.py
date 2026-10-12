# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-13
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
FastAPI app: a health check and a small notes API.

Notes are stored in the database DATABASE_URL points to (see app/db.py): PostgreSQL in
Docker Compose, a local SQLite file otherwise. The tables are created at startup.

Requires: fastapi, uvicorn and sqlalchemy from requirements.txt.

Run: uvicorn app.main:app --reload
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import NoteRow, create_tables, get_session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Creates the tables once at startup (FastAPI requires the async form here)."""
    create_tables()
    yield


app = FastAPI(title="study-cloud", lifespan=lifespan)

# a database session per request, passed in by FastAPI
SessionDep = Annotated[Session, Depends(get_session)]


class NoteIn(BaseModel):
    """What a client sends to create a note."""

    text: str


class Note(NoteIn):
    """A stored note, with the id the database gave it."""

    model_config = ConfigDict(from_attributes=True)  # can be built from a NoteRow

    id: int


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check; Kubernetes will call this in step 3."""
    return {"status": "ok"}


@app.get("/notes")
def list_notes(session: SessionDep) -> list[Note]:
    """Returns all notes, oldest first."""
    rows = session.scalars(select(NoteRow).order_by(NoteRow.id))
    return [Note.model_validate(row) for row in rows]


@app.post("/notes", status_code=201)
def create_note(note: NoteIn, session: SessionDep) -> Note:
    """Stores a note and returns it with its new id."""
    row = NoteRow(text=note.text)
    session.add(row)
    session.commit()  # write it; the database assigns the id
    session.refresh(row)  # read the id back
    return Note.model_validate(row)


@app.get("/notes/{note_id}")
def get_note(note_id: int, session: SessionDep) -> Note:
    """Returns one note; 404 if the id doesn't exist."""
    row = session.get(NoteRow, note_id)
    if row is None:
        raise HTTPException(status_code=404, detail="note not found")
    return Note.model_validate(row)
