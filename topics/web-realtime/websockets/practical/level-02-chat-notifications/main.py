from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, username: str) -> None:
        await websocket.accept()
        self.active_connections[websocket] = username
        await self.broadcast("notification", f"{username} joined the chat")

    async def disconnect(self, websocket: WebSocket) -> None:
        username = self.active_connections.pop(websocket, None)
        if username is not None:
            await self.broadcast("notification", f"{username} left the chat")

    async def broadcast(self, event_type: str, message: str) -> None:
        disconnected_clients: list[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await connection.send_json(
                    {
                        "type": event_type,
                        "message": message,
                    }
                )
            except RuntimeError:
                disconnected_clients.append(connection)

        for connection in disconnected_clients:
            await self.disconnect(connection)


manager = ConnectionManager()


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str) -> None:
    await manager.connect(websocket, username)

    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast("chat_message", f"{username}: {message}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
