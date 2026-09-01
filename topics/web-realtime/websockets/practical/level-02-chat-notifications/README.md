# Level 02: Chat Notifications

This level builds a small WebSocket chat app in parts.

The goal is to move from "one client talks to the server" to "many clients share one live chat room".

## Parts

| Part | Status | Focus |
| --- | --- | --- |
| 1 | Done | Broadcast messages to all connected clients and show join/leave notifications |
| 2 | Next | Add message validation and clearer error handling |
| 3 | Later | Add browser notification permission for messages received while the tab is unfocused |

## Current Scope

Part 1 intentionally keeps the app simple:

- One global chat room.
- No database.
- No authentication.
- No private messages.
- No message history after refresh.

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

Use a different display name in each tab. When one tab sends a message, the other tab receives it without making a new HTTP request.

## What To Notice

- `ConnectionManager` stores active WebSocket connections.
- The `/ws/{username}` endpoint accepts one WebSocket connection per browser tab.
- A chat message is sent once by the client, then broadcast by the server.
- Join and leave notifications are also broadcast events.
- All connected clients receive the same room events.

## Important Limitation

This implementation stores connections in memory. That is fine for learning and for a single server process.

In production, this does not automatically work across multiple server instances. If you run several FastAPI processes, each process only knows about its own WebSocket connections. Later levels should introduce Redis Pub/Sub, NATS, Kafka, or another shared messaging layer.

