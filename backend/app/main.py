"""
main.py  -  FastAPI application: REST API for the laptop frontend.

Run with:   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
Docs:       http://localhost:8000/docs   (automatic Swagger UI)
"""
from datetime import timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import ws_device
from .db import Base, Event, Reading, engine, get_db
from .schemas import (EventCreate, EventOut, EventPatch, FaceCommand,
                      PomodoroCommand, ReadingOut)
from .state import send_to_device, state

Base.metadata.create_all(engine)   # creates tables on first run

app = FastAPI(title="Nimbus Backend", version="0.1")

# CORS (Cross-Origin Resource Sharing): lets the frontend, running on a different
# port, call this API. "*" is fine for a local project, not for production.
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.include_router(ws_device.router)


# ---------------- health and status ----------------
@app.get("/health")
def health():
    return {"status": "ok", "device_online": state.online}


@app.get("/api/status")
def status():
    """Everything the dashboard's live page needs, in one call."""
    return {
        "device_online": state.online,
        "last_seen": state.last_seen.isoformat() if state.last_seen else None,
        "mood": state.mood,
        "latest": state.latest,
    }


# ---------------- readings ----------------
@app.get("/api/readings/latest", response_model=ReadingOut)
def latest_reading(db: Session = Depends(get_db)):
    row = db.scalars(select(Reading).order_by(Reading.id.desc())).first()
    if row is None:
        raise HTTPException(404, "No readings yet")
    return row


@app.get("/api/readings", response_model=list[ReadingOut])
def list_readings(limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 1000))
    rows = db.scalars(select(Reading).order_by(Reading.id.desc()).limit(limit)).all()
    return list(reversed(rows))        # oldest first, good for charts


# ---------------- events (exams, classes, deadlines) ----------------
@app.get("/api/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.scalars(select(Event).order_by(Event.due_time)).all()


@app.post("/api/events", response_model=EventOut, status_code=201)
def create_event(body: EventCreate, db: Session = Depends(get_db)):
    due = body.due_time
    if due.tzinfo is not None:         # convert to naive UTC before storing
        due = due.astimezone(timezone.utc).replace(tzinfo=None)
    ev = Event(title=body.title, type=body.type, due_time=due)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


@app.patch("/api/events/{event_id}", response_model=EventOut)
def mark_event(event_id: int, body: EventPatch, db: Session = Depends(get_db)):
    ev = db.get(Event, event_id)
    if ev is None:
        raise HTTPException(404, "Event not found")
    ev.done = body.done
    db.commit()
    db.refresh(ev)
    return ev


@app.delete("/api/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(Event, event_id)
    if ev is None:
        raise HTTPException(404, "Event not found")
    db.delete(ev)
    db.commit()


# ---------------- commands to the ESP32 ----------------
@app.post("/api/device/face")
async def set_face(body: FaceCommand):
    ok = await send_to_device({"type": "face", "mood": body.mood})
    if not ok:
        raise HTTPException(503, "Device is offline")
    state.mood = body.mood
    return {"sent": True, "mood": body.mood}


@app.post("/api/device/pomodoro")
async def start_pomodoro(body: PomodoroCommand):
    ok = await send_to_device({"type": "pomodoro", "minutes": body.minutes})
    if not ok:
        raise HTTPException(503, "Device is offline")
    return {"sent": True, "minutes": body.minutes}
