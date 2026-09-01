# WebSockets and WebRTC

This note explains two major browser technologies used for real-time communication: WebSocket and WebRTC.

They are often mentioned together because both allow low-latency communication from the browser, but they are not interchangeable. They have different architectures, transports, failure modes, scaling models, and operational concerns.

The short version:

- WebSocket is usually the right choice when a browser needs a persistent real-time connection to a backend service.
- WebRTC is usually the right choice when browsers or clients need low-latency peer-to-peer audio, video, screen sharing, or data transfer.

## Practical Track

- [WebSocket practical levels](websockets/practical)

## The Problem They Solve

Traditional HTTP follows a request-response model:

1. The client sends a request.
2. The server sends a response.
3. The exchange ends.

That works well for pages, APIs, forms, and most CRUD systems. It is less ideal when the server needs to push information to the client immediately.

Examples:

- A chat message arrives.
- A stock price changes.
- A multiplayer game state updates.
- A dashboard metric changes.
- A remote participant sends audio or video.
- A browser tab needs to exchange data directly with another browser tab.

Before real-time browser protocols became common, applications often used polling or long polling.

Polling means the client repeatedly asks the server if anything changed. This is simple, but wasteful and not truly real time.

Long polling keeps the request open until the server has something to send. This improves latency, but still uses an HTTP request-response shape.

WebSocket and WebRTC solve this more directly.

## WebSocket

WebSocket is a protocol that gives the browser and server a persistent, bidirectional communication channel.

The connection starts as an HTTP request. The client asks the server to upgrade the connection from HTTP to WebSocket. If the server accepts, the protocol switches, and both sides can send messages over the same long-lived connection.

After the upgrade, the connection is no longer ordinary request-response HTTP. It becomes a continuous message channel.

### WebSocket Mental Model

Think of WebSocket as:

```text
Browser <==== persistent TCP connection ====> Server
```

The browser connects to the backend. The backend keeps the connection open. Either side can send messages at any time.

This is very useful when the backend is the source of truth and clients need live updates.

### WebSocket Transport

WebSocket runs over TCP.

TCP provides:

- Reliable delivery.
- Ordered delivery.
- Retransmission of lost packets.
- Congestion control.

This makes WebSocket easy to reason about for application messages. If the server sends message A and then message B, the client receives A before B, assuming the connection remains alive.

The downside is that TCP can introduce head-of-line blocking. If one packet is lost, later data may be delayed until the missing packet is retransmitted. For many application messages this is acceptable. For real-time audio and video, this can be harmful because late media packets are often useless.

### Common WebSocket Use Cases

WebSocket is a good fit for:

- Chat applications.
- Live notifications.
- Collaborative editing coordination.
- Live dashboards.
- Trading or market data interfaces.
- Multiplayer games where the server owns the game state.
- Presence systems, such as online or typing indicators.
- Job progress updates.
- Control channels for distributed systems.

It is especially useful when communication is client-server and the server must authenticate, authorize, validate, persist, broadcast, or coordinate messages.

### WebSocket Pros

- Simple client-server model.
- Works naturally with backend application architecture.
- Uses reliable and ordered delivery through TCP.
- Easy to put behind authentication and authorization.
- Easier to observe, log, rate limit, and control than peer-to-peer traffic.
- Good for messages where correctness matters more than ultra-low latency.
- Supported by browsers and most backend frameworks.

### WebSocket Cons

- Not peer-to-peer.
- Server must handle every connected client.
- Long-lived connections require careful scaling.
- TCP head-of-line blocking can hurt real-time media.
- Load balancing is more complicated than stateless HTTP.
- Connection state must be managed during deploys, restarts, and failures.
- Binary streaming is possible, but WebSocket is not optimized for browser audio/video calling in the way WebRTC is.

### WebSocket Implementation Concerns

When implementing WebSocket, pay attention to the following.

#### Authentication

Authenticate the connection during the initial HTTP upgrade or immediately after connection establishment.

Common approaches:

- Use an HTTP-only session cookie.
- Pass a short-lived token in a header when the client supports it.
- Pass a short-lived token in the query string only if you understand the logging risk.
- Send an authentication message as the first WebSocket message.

Avoid long-lived bearer tokens in URLs because URLs often end up in logs, metrics, proxies, and browser history.

#### Authorization

Do not trust a client-side room ID, tenant ID, document ID, or user ID. Validate every subscription and action on the server.

#### Connection Lifecycle

WebSocket connections are long-lived, but networks are unreliable.

You need to handle:

- Connect.
- Disconnect.
- Reconnect.
- Duplicate connections.
- Heartbeats or ping/pong.
- Idle timeouts.
- Server restarts.
- Browser sleep and mobile network changes.

The client should usually reconnect with backoff instead of retrying in a tight loop.

#### Message Design

Define a clear message shape.

Example:

```json
{
  "type": "chat.message.created",
  "requestId": "req_123",
  "payload": {
    "roomId": "room_456",
    "text": "hello"
  }
}
```

Good message design includes:

- A message type.
- A schema per type.
- Versioning strategy.
- Correlation or request IDs.
- Error messages.
- Idempotency where needed.
- Limits on message size.

Do not let the WebSocket become an unstructured stream of random JSON.

#### Backpressure

A client can be slow. A network can be slow. A server can produce messages faster than a client can consume them.

Plan for:

- Send queue limits.
- Dropping non-critical messages.
- Disconnecting clients that cannot keep up.
- Separating critical messages from high-volume updates.
- Compressing carefully, because compression can increase CPU and security risk.

#### Scaling

HTTP APIs are often stateless. WebSocket servers are usually stateful because each server owns active connections.

Common scaling concerns:

- Load balancers must support WebSocket upgrades.
- Idle timeouts must be configured correctly.
- You may need sticky sessions.
- Broadcast across instances needs Redis, NATS, Kafka, Postgres LISTEN/NOTIFY, or another pub/sub mechanism.
- Deployments should drain connections gracefully.

#### Security

Important security concerns:

- Validate the `Origin` header for browser clients.
- Authenticate and authorize every action.
- Rate limit connection attempts and message rates.
- Limit payload size.
- Validate message schemas.
- Avoid sending sensitive data to broad subscriptions.
- Protect against cross-site WebSocket hijacking when using cookies.
- Use `wss://` in production.

## WebRTC

WebRTC is a set of browser APIs and protocols for real-time communication between peers.

It is commonly used for:

- Audio calls.
- Video calls.
- Screen sharing.
- Peer-to-peer data channels.
- Low-latency media streaming.

WebRTC is not just one protocol. It is a full stack for negotiating connections, traversing NATs, encrypting media, sending streams, adapting bitrate, and optionally exchanging arbitrary data.

### WebRTC Mental Model

Think of WebRTC as:

```text
Browser A <==== low-latency media/data path ====> Browser B
       \                                      /
        \                                    /
         ===== signaling server needed =====
```

The media or data may flow directly between peers. However, the peers still need a signaling mechanism to find each other and exchange connection information.

The signaling server is not defined by WebRTC. You build it yourself using HTTP, WebSocket, Server-Sent Events, or another messaging mechanism.

### WebRTC Transport

WebRTC usually prefers UDP.

UDP does not guarantee delivery or ordering. That sounds worse than TCP, but it is often better for real-time media.

For audio and video, late packets are often useless. If a video frame is delayed too long, the application should continue with newer frames instead of waiting. This is why low latency is often more important than perfect reliability.

WebRTC can also use TCP or relay traffic through TURN servers when UDP peer-to-peer connectivity fails.

The precise connection path depends on the network.

### Core WebRTC Concepts

#### Signaling

Signaling is the process where peers exchange metadata needed to establish a WebRTC connection.

Signaling commonly exchanges:

- Session descriptions.
- ICE candidates.
- Media capabilities.
- Network addresses.
- Call state, such as offer, answer, join, leave, mute, and hang up.

WebRTC does not specify how signaling must be implemented. Many applications use WebSocket because signaling itself is a real-time client-server messaging problem.

#### SDP

SDP stands for Session Description Protocol.

In WebRTC, SDP describes media capabilities and connection parameters. Peers exchange SDP offers and answers during negotiation.

As an application developer, you usually do not hand-write SDP. You pass it between peers through your signaling server.

#### ICE

ICE stands for Interactive Connectivity Establishment.

ICE is the process WebRTC uses to discover the best path between peers. It tries possible network routes and selects a working candidate pair.

#### STUN

STUN helps a client discover its public-facing network address as seen from the internet.

This is useful because most clients are behind NAT. The local private address, such as `192.168.x.x`, is not enough for another peer to connect.

#### TURN

TURN is a relay service.

If peers cannot connect directly, traffic can be relayed through a TURN server.

TURN improves reliability across restrictive networks, but it increases cost because media traffic passes through your infrastructure.

#### DataChannel

WebRTC DataChannel allows peers to send arbitrary data, not just audio or video.

DataChannel can be configured for different reliability and ordering behavior. This makes it useful for low-latency peer-to-peer data, such as game state, cursor movement, file transfer chunks, or collaboration events.

### Common WebRTC Use Cases

WebRTC is a good fit for:

- Video meetings.
- Voice calls.
- Screen sharing.
- Telehealth or online classrooms.
- Browser-based live support.
- Peer-to-peer file transfer.
- Low-latency multiplayer communication.
- Remote control or remote assistance.
- Real-time collaboration where direct peer data exchange is useful.

WebRTC is especially useful when media latency matters and when sending all traffic through the application server would be too slow or expensive.

### WebRTC Pros

- Designed for real-time audio and video.
- Low-latency by default.
- Can use peer-to-peer paths.
- Encrypted by default.
- Supports adaptive media quality.
- Supports data channels, not only media.
- Reduces backend bandwidth when direct peer-to-peer connections work.

### WebRTC Cons

- More complex than WebSocket.
- Requires signaling, even though signaling is not specified by WebRTC.
- NAT traversal can be difficult.
- TURN servers are often required for reliability.
- Debugging connection failures can be hard.
- Multi-party calls often need SFU or MCU infrastructure.
- Browser behavior and network conditions can vary.
- Operational costs can become significant if relayed media is common.

### WebRTC Implementation Concerns

When implementing WebRTC, pay attention to the following.

#### Signaling Design

You need a signaling server.

The signaling layer should handle:

- Room creation.
- Peer identity.
- Offer and answer exchange.
- ICE candidate exchange.
- Join and leave events.
- Call state.
- Reconnects.
- Authorization.

WebSocket is commonly used for signaling because signaling messages need to move quickly between clients and server.

#### NAT Traversal

Many users are behind routers, firewalls, corporate networks, VPNs, or mobile carriers.

You should configure:

- STUN servers for public address discovery.
- TURN servers for relay fallback.
- Monitoring for direct versus relayed connection rates.

If you do not provide TURN, your WebRTC app may work during development and fail for real users on restrictive networks.

#### Media Quality

Real-time media must adapt to network conditions.

You need to consider:

- Bitrate adaptation.
- Resolution changes.
- Frame rate changes.
- Audio prioritization.
- Packet loss.
- Jitter.
- Device CPU usage.
- Camera and microphone permissions.

For calls, audio quality is often more important than video quality. A meeting with degraded video can still work. A meeting with broken audio usually cannot.

#### Topology

For one-to-one calls, peer-to-peer can work well.

For group calls, pure mesh peer-to-peer becomes expensive because every participant sends media to every other participant.

Common topologies:

- Peer-to-peer: simple for one-to-one calls.
- Mesh: each participant connects to every other participant; acceptable only for small rooms.
- SFU: Selective Forwarding Unit receives media streams and forwards them to others; common for production group calls.
- MCU: Multipoint Control Unit mixes streams server-side; more expensive but useful for some cases.

#### Permissions and Privacy

WebRTC commonly uses camera, microphone, and screen sharing.

You need to handle:

- Permission prompts.
- Devices being denied.
- Devices changing.
- Muting and unmuting.
- Camera off state.
- Screen share stop events.
- Clear user indicators for active capture.

Never hide or obscure whether audio, video, or screen sharing is active.

#### Security

Important security concerns:

- Authenticate users before allowing them into rooms.
- Authorize room access.
- Avoid leaking SDP or ICE data to unauthorized users.
- Use short-lived TURN credentials.
- Treat signaling messages as untrusted input.
- Protect against room enumeration.
- Rate limit room joins and signaling messages.
- Be careful with screen sharing because it can expose sensitive information.

## WebSocket vs WebRTC

| Category | WebSocket | WebRTC |
| --- | --- | --- |
| Primary purpose | Real-time client-server messaging | Real-time peer media and data |
| Typical transport | TCP | Usually UDP, with TCP/TURN fallback |
| Communication model | Client to server | Peer to peer, or via media servers |
| Browser API complexity | Lower | Higher |
| Backend complexity | Moderate | Higher |
| Best for | Events, commands, notifications, chat, dashboards | Audio, video, screen sharing, low-latency peer data |
| Reliability | Reliable and ordered through TCP | Configurable for data; media prioritizes timeliness |
| Latency | Low, but TCP can block on packet loss | Very low, optimized for real-time media |
| Scaling pressure | Many persistent server connections | Signaling plus possible TURN/SFU media infrastructure |
| Observability | Easier because traffic goes through server | Harder when traffic is peer-to-peer |
| Production difficulty | Medium | High |

## Choosing Between Them

Use WebSocket when:

- The application is client-server.
- The server is the source of truth.
- Messages should be reliable and ordered.
- You need subscriptions, notifications, commands, or live updates.
- You want simpler infrastructure than WebRTC.

Use WebRTC when:

- You need audio, video, or screen sharing.
- You need very low-latency peer-to-peer communication.
- Sending all media through your app server would be too expensive or too slow.
- You can invest in signaling, STUN, TURN, and possibly SFU infrastructure.

Use both when:

- You need WebRTC for media and WebSocket for signaling.
- You need WebRTC for peer data and WebSocket for backend coordination.
- You need a server-authoritative system plus peer-to-peer optimization.

## Example Architectures

### Chat App

```text
Browser A ----\
               WebSocket Server ---- Database
Browser B ----/
```

Use WebSocket. The server can authenticate users, persist messages, enforce room membership, and broadcast new messages.

### Video Call

```text
Browser A <==== WebRTC media path ====> Browser B
    |                                      |
    ===== WebSocket signaling server ======
```

Use WebRTC for media. Use WebSocket for signaling.

### Live Dashboard

```text
Backend Workers ---- Pub/Sub ---- WebSocket Server ---- Browser
```

Use WebSocket. The server pushes updates when metrics change.

### Group Video Meeting

```text
Browser A ----\
Browser B ----- SFU ---- Browser C
Browser D ----/

All clients also connect to a signaling server.
```

Use WebRTC with an SFU. Avoid full mesh for larger groups.

## Common Mistakes

- Assuming WebRTC means no servers are needed.
- Building WebRTC without TURN and thinking it is production ready.
- Using WebSocket for video calls when WebRTC is the correct tool.
- Using WebRTC for simple server notifications when WebSocket is simpler.
- Forgetting authorization on subscriptions or rooms.
- Ignoring reconnect behavior.
- Ignoring backpressure and message queue growth.
- Treating real-time systems as stateless HTTP APIs.
- Not testing on mobile networks, VPNs, and restrictive corporate networks.
- Not planning observability for connection failures.

## Production Checklist

For WebSocket:

- Use `wss://` in production.
- Authenticate connections.
- Authorize subscriptions and actions.
- Validate every message schema.
- Define message size limits.
- Add ping/pong or heartbeat handling.
- Implement reconnect with backoff.
- Handle duplicate connections.
- Configure load balancer WebSocket support.
- Configure idle timeouts intentionally.
- Add pub/sub if multiple backend instances need to broadcast.
- Monitor connection count, message rate, send queue size, errors, and disconnect reasons.

For WebRTC:

- Build a signaling server.
- Authenticate and authorize room access.
- Configure STUN.
- Configure TURN with short-lived credentials.
- Track ICE connection states.
- Handle permission denial for camera, microphone, and screen sharing.
- Handle device changes.
- Test peer-to-peer and TURN-relayed paths.
- Decide on peer-to-peer, mesh, SFU, or MCU topology.
- Monitor packet loss, jitter, bitrate, round-trip time, and connection failure reasons.
- Test on Wi-Fi, mobile data, VPN, and restrictive networks.

## Final Mental Model

WebSocket is a real-time pipe between a client and your server.

WebRTC is a real-time media and data engine between peers, with servers used for signaling, NAT traversal, and sometimes media relay or forwarding.

The important difference is not only TCP versus UDP. The more important difference is the architecture:

- WebSocket centralizes communication through your backend.
- WebRTC tries to create low-latency paths between peers.

That architectural difference drives the use cases, complexity, scaling model, and operational risk.
