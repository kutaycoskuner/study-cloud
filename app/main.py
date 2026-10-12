# -----------------------------------------------------------------------------------------
#   author          : Kutay Coskuner
#   ai-contributors : Claude Opus 5.5 (claude-opus-5-5)
#   last update     : 2026-10-12
#   disclaimer      : Provided as is, without warranty of any kind; use at your own risk.
#                     Check outputs before relying on them.
# -----------------------------------------------------------------------------------------
"""
FastAPI app: a health check and a small notes API.

Notes are kept in memory, so they are lost on every restart; a database replaces the
dict in step 2.

Requires: fastapi and uvicorn from requirements.txt.

Run: uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="study-cloud")


class NoteIn(BaseModel):
    """What a client sends to create a note."""

    text: str


class Note(NoteIn):
    """A stored note, with the id the server gave it."""

    id: int


# id -> note; replaced by the database in step 2
notes: dict[int, Note] = {}


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check; Kubernetes will call this in step 3."""
    return {"status": "ok"}


@app.get("/notes")
def list_notes() -> list[Note]:
    """Returns all notes."""
    return list(notes.values())


@app.post("/notes", status_code=201)
def create_note(note: NoteIn) -> Note:
    """Stores a note and returns it with its new id."""
    new_id = max(notes, default=0) + 1
    notes[new_id] = Note(id=new_id, text=note.text)
    return notes[new_id]


@app.get("/notes/{note_id}")
def get_note(note_id: int) -> Note:
    """Returns one note; 404 if the id doesn't exist."""
    if note_id not in notes:
        raise HTTPException(status_code=404, detail="note not found")
    return notes[note_id]
