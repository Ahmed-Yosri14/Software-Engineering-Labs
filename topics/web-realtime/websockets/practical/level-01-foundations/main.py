from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_text("connection accepted")

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"received '{message}'")
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
