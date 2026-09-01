from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"
USERNAME_ALREADY_TAKEN_CLOSE_CODE = 1008
INVALID_JOIN_CLOSE_CODE = 1008


def normalize_username(username: str) -> str:
    return username.strip().lower()


def normalize_room_name(room_name: str) -> str:
    return room_name.strip().lower()


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, dict[WebSocket, str]] = {}
        self.room_names: dict[str, str] = {}
        self.connection_rooms: dict[WebSocket, str] = {}

    def list_rooms(self) -> list[dict[str, int | str]]:
        return [
            {
                "name": self.room_names[room_key],
                "participant_count": len(connections),
            }
            for room_key, connections in sorted(self.rooms.items())
        ]

    def is_username_taken(self, room_key: str, username: str) -> bool:
        normalized_username = normalize_username(username)
        return normalized_username in {
            normalize_username(active_username)
            for active_username in self.rooms.get(room_key, {}).values()
        }

    async def connect(self, websocket: WebSocket, room_name: str, username: str) -> bool:
        await websocket.accept()

        clean_room_name = room_name.strip()
        clean_username = username.strip()
        if not clean_room_name or not clean_username:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "Room name and display name are required.",
                }
            )
            await websocket.close(code=INVALID_JOIN_CLOSE_CODE)
            return False

        room_key = normalize_room_name(clean_room_name)
        if self.is_username_taken(room_key, clean_username):
            await websocket.send_json(
                {
                    "type": "error",
                    "message": f"'{clean_username}' is already connected in '{clean_room_name}'. Choose another name.",
                }
            )
            await websocket.close(code=USERNAME_ALREADY_TAKEN_CLOSE_CODE)
            return False

        self.rooms.setdefault(room_key, {})
        self.room_names.setdefault(room_key, clean_room_name)
        self.rooms[room_key][websocket] = clean_username
        self.connection_rooms[websocket] = room_key

        await self.broadcast(
            room_key,
            "notification",
            f"{clean_username} joined {self.room_names[room_key]}",
        )
        return True

    async def disconnect(self, websocket: WebSocket) -> None:
        room_key = self.connection_rooms.pop(websocket, None)
        if room_key is None:
            return

        room_connections = self.rooms.get(room_key)
        if room_connections is None:
            return

        username = room_connections.pop(websocket, None)
        if username is None:
            return

        if not room_connections:
            self.rooms.pop(room_key, None)
            self.room_names.pop(room_key, None)
            return

        await self.broadcast(
            room_key,
            "notification",
            f"{username} left {self.room_names[room_key]}",
        )

    async def broadcast(self, room_key: str, event_type: str, message: str) -> None:
        disconnected_clients: list[WebSocket] = []

        for connection in list(self.rooms.get(room_key, {})):
            try:
                await connection.send_json(
                    {
                        "type": event_type,
                        "room": self.room_names[room_key],
                        "message": message,
                    }
                )
            except (RuntimeError, WebSocketDisconnect):
                disconnected_clients.append(connection)

        for connection in disconnected_clients:
            await self.disconnect(connection)


manager = ConnectionManager()


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(INDEX_FILE)


@app.get("/rooms")
async def list_rooms() -> list[dict[str, int | str]]:
    return manager.list_rooms()


@app.websocket("/ws/{room_name}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, username: str) -> None:
    connected = await manager.connect(websocket, room_name, username)
    if not connected:
        return

    room_key = normalize_room_name(room_name)
    clean_username = username.strip()

    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast(room_key, "chat_message", f"{clean_username}: {message}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
