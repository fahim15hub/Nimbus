# Nimbus - Step 1 and 2 (backend + simulator)

## Setup (once)
```
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
pip install -r ../simulator/requirements.txt
```

## Run
Terminal 1 (backend):
```
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Terminal 2 (fake ESP32):
```
cd simulator
python simulator.py
```
Open http://localhost:8000/docs and try the endpoints.

## Find your laptop IP (for the real ESP32 later)
Windows: `ipconfig`  ->  "IPv4 Address". Linux: `ip addr`.
The ESP32 will connect to `ws://<that-ip>:8000/ws/device`.
Allow port 8000 in Windows Firewall, and keep laptop + ESP32 on the same WiFi.
