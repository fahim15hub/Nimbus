"""
ws_device.py  -  WebSocket endpoint the ESP32 connects to.

Flow:  ESP32 connects to  ws://<laptop-ip>:8000/ws/device
Text frames   = JSON messages (telemetry, events)
Binary frames = audio (used later in the voice step)
"""
import json

from fastapi import APIRouter, WebSocket
from pydantic import ValidationError

from .db import Reading, SessionLocal
from .schemas import TelemetryIn
from .state import state

router = APIRouter()


def save_reading(t: TelemetryIn) -> None:
    db = SessionLocal()
    try:
        db.add(Reading(
            temperature=t.temp, humidity=t.hum, light=t.light,
            presence=t.presence, distance=t.dist,
        ))
        db.commit()
    finally:
        db.close()


async def handle_text(ws: WebSocket, raw: str) -> None:
    # 1) Parse JSON. A broken message must never crash the server.
    try:
        data = json.loads(raw)
        msg_type = data.get("type")
    except (json.JSONDecodeError, AttributeError):
        await ws.send_json({"type": "error", "detail": "invalid JSON"})
        return

    # 2) Decide what to do based on the message type.
    if msg_type == "telemetry":
        try:
            t = TelemetryIn(**{k: v for k, v in data.items() if k != "type"})
        except ValidationError as e:
            await ws.send_json({"type": "error", "detail": e.errors()[0]["msg"]})
            return
        state.latest = t.model_dump()
        save_reading(t)

    elif msg_type == "event":
        # e.g. {"type":"event","name":"pomodoro_done","minutes":25}
        print(f"[device event] {data}")

    elif msg_type in ("audio_start", "audio_end"):
        # Voice step comes later; for now just log it.
        print(f"[device] {msg_type}")

    else:
        await ws.send_json({"type": "error", "detail": f"unknown type: {msg_type}"})


@router.websocket("/ws/device")
async def device_socket(ws: WebSocket) -> None:
    await ws.accept()
    state.ws = ws
    state.touch()
    print("[ws] ESP32 connected")
    await ws.send_json({"type": "hello", "v": 1})

    try:
        while True:
            msg = await ws.receive()          # waits for the next frame
            if msg["type"] == "websocket.disconnect":
                break
            state.touch()
            if msg.get("text") is not None:
                await handle_text(ws, msg["text"])
            elif msg.get("bytes") is not None:
                pass  # audio chunks will be handled in the voice step
    finally:
        if state.ws is ws:
            state.ws = None
        print("[ws] ESP32 disconnected")
