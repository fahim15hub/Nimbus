"""
schemas.py  -  the "contract" between ESP32, backend and frontend.

Pydantic checks that incoming data has the right shape and types.
If data is wrong, Pydantic raises an error instead of letting bad data in.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer

# The only moods the face is allowed to show (same list in firmware).
Mood = Literal[
    "happy", "focused", "sleepy", "worried",
    "surprised", "listening", "thinking", "talking",
]

EventType = Literal["exam", "class", "deadline", "reminder"]


# ---------- ESP32 -> backend (WebSocket) ----------
class TelemetryIn(BaseModel):
    """One sensor reading sent by the ESP32."""
    temp: Optional[float] = None          # temperature in degrees Celsius
    hum: Optional[float] = Field(None, ge=0, le=100)   # humidity in percent
    light: Optional[int] = None           # raw LDR (Light Dependent Resistor) value
    presence: bool = False                # PIR (Passive Infrared) sensor: someone is there?
    dist: Optional[int] = None            # ultrasonic distance in centimetres


# ---------- Backend -> frontend (REST) ----------
class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    time: datetime
    temperature: Optional[float]
    humidity: Optional[float]
    light: Optional[int]
    presence: bool
    distance: Optional[int]

    @field_serializer("time")
    def _time_as_utc(self, v: datetime) -> str:
        # Times are stored in UTC (Coordinated Universal Time); add "Z" to say so.
        return v.isoformat() + "Z"


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    type: EventType
    due_time: datetime


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    type: str
    due_time: datetime
    done: bool

    @field_serializer("due_time")
    def _due_as_utc(self, v: datetime) -> str:
        return v.isoformat() + "Z"


class EventPatch(BaseModel):
    done: bool


# ---------- Frontend -> backend -> ESP32 commands ----------
class FaceCommand(BaseModel):
    mood: Mood


class PomodoroCommand(BaseModel):
    minutes: int = Field(ge=1, le=180)
