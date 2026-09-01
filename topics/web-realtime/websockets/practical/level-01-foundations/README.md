# Level 01: WebSocket Foundations

This first practical step builds the smallest useful WebSocket application with FastAPI.

The goal is to learn the connection lifecycle:

1. The browser loads an HTML page from FastAPI.
2. The browser opens a WebSocket connection to `/ws`.
3. FastAPI accepts the WebSocket connection.
4. The browser sends text messages.
5. The server receives each message and sends a response back over the same connection.

At this level, there is no broadcast, no rooms, no authentication, no database, and no reconnect logic. Those belong in later levels.

## Run

From this directory:

```powershell
pip install -r requirements.txt
uvicorn main:app --reload --port 8010
```

Then open:

```text
http://127.0.0.1:8010
```

This lab pins FastAPI to the Pydantic 1 generation because the current repo virtualenv uses Python 3.14 on Mingw, where the newer `pydantic-core` dependency does not install cleanly.

## What To Notice

- `main.py` contains the FastAPI application and WebSocket endpoint.
- `index.html` contains the browser UI and client-side WebSocket code.
- The HTTP route `/` serves `index.html`.
- The WebSocket route `/ws` handles the real-time connection.
- The server must call `await websocket.accept()` before sending or receiving messages.
- `receive_text()` waits until the client sends a message.
- `send_text()` sends data back without creating a new HTTP response.
- A WebSocket connection stays open until the browser, network, or server closes it.
