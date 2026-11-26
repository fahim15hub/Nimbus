"""
state.py  -  shared in-memory state about the ESP32 connection.

Only one device ("bot1") for now. Other modules import `state` from here.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import WebSocket


class DeviceState:
    def __init__(self) -> None:
        self.ws: Optional[WebSocket] = None      # the live WebSocket, or None if offline
        self.last_seen: Optional[datetime] = None
        self.latest: Optional[dict] = None       # most recent telemetry
        self.mood: str = "happy"

    @property
    def online(self) -> bool:
        return self.ws is not None

    def touch(self) -> None:
        self.last_seen = datetime.now(timezone.utc)


state = DeviceState()


async def send_to_device(payload: dict) -> bool:
    """Send a JSON command to the ESP32. Returns False if it is not connected."""
    if state.ws is None:
        return False
    try:
        await state.ws.send_json(payload)
        return True
    except Exception:
        return False
