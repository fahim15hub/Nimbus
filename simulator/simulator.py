"""
simulator.py  -  pretends to be the ESP32 so you can build the backend
before the hardware is ready.

Usage:  python simulator.py                       (connects to localhost)
        python simulator.py ws://192.168.0.10:8000/ws/device
"""
import asyncio
import json
import random
import sys

import websockets

URL = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8000/ws/device"


async def send_telemetry(ws):
    temp, hum = 29.0, 60.0
    while True:
        # Random walk: small changes each time, like a real sensor.
        temp += random.uniform(-0.3, 0.4)
        hum += random.uniform(-1, 1)
        data = {
            "type": "telemetry",
            "temp": round(temp, 1),
            "hum": round(max(0, min(100, hum)), 1),
            "light": random.randint(300, 600),
            "presence": random.random() > 0.2,
            "dist": random.randint(35, 60),
        }
        await ws.send(json.dumps(data))
        print("sent:", data)
        await asyncio.sleep(2)


async def listen(ws):
    async for message in ws:
        print("<< from backend:", message)


async def main():
    while True:                              # auto-reconnect, like the real firmware
        try:
            async with websockets.connect(URL) as ws:
                print("connected to", URL)
                await asyncio.gather(send_telemetry(ws), listen(ws))
        except Exception as e:
            print("connection lost:", e, "- retrying in 3 s")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
