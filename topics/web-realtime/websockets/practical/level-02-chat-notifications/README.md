# Level 02: Chat Notifications

This level builds a small WebSocket chat app in parts.

The goal is to move from "one client talks to the server" to "many clients share one live chat room".

## Current Scope

The current app intentionally keeps the persistence model simple:

- No database.
- No authentication.
- No private messages.
- No message history after refresh.
- Rooms exist only while they have connected users.
- Duplicate display names are rejected inside the same room.

This keeps the focus on the most important WebSocket idea for chat: the server tracks active connections and broadcasts events to them.

## Run

From this directory:

```powershell
pip install -r requirements.txt
uvicorn main:app --reload --port 8020
```

Then open two browser tabs:

```text
http://127.0.0.1:8020
```

Set a display name first.

Create a room by clicking `Create New Room`, entering a room name in the modal, and confirming.

Join an existing room by clicking the room item's `Join` button.

Use a different display name in each tab for the same room. When one tab sends a message, the other tab receives it without making a new HTTP request.

Try opening a third tab with a display name that is already connected in the same room. The server rejects the WebSocket connection and the browser shows an error.

Using the same display name in a different room is allowed.

If you are already connected to one room and try to join another room, the app shows a confirmation modal before closing the current WebSocket connection.

After joining a room, the sidebar hides the display-name form. When reopened, it shows other active rooms only. Each room item has its own `Join` button.

Leaving a room also uses a confirmation modal because it closes the active WebSocket connection.

## What To Notice

- `ConnectionManager` stores active WebSocket connections by room.
- The `/rooms` HTTP route lists currently active rooms.
- The `/ws/{room_name}/{username}` endpoint accepts one WebSocket connection per browser tab.
- Joining a room that does not exist creates it.
- The browser can close the current WebSocket and open another one when switching rooms.
- While connected, the browser reuses the current display name when joining another room.
- A chat message is sent once by the client, then broadcast by the server to that room.
- Join and leave notifications are also room events.
- Only clients in the same room receive the same room events.
- The server stores normalized usernames per room, so `Yosry` and `yosry` count as the same active name inside that room.
- Duplicate username checks must happen on the server because browser checks can be bypassed.