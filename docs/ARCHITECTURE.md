# Architecture

ChatApp separates protocol framing, TCP networking, browser transport, administration, and UI so
the individual layers remain testable.

## Runtime topology

```text
Browser
  │ WebSocket
  ▼
chatapp.web / FastAPI
  │ one ChatClient per browser connection
  ▼
ChatServer ◄──────── terminal ChatClient
  │
  └─────────────── terminal ChatClient
```

The browser gateway is an adapter around the existing TCP client. It does not own chat state.

## Components

### `chatapp.protocol`

Defines the newline-delimited UTF-8 wire format. `LineBuffer` handles TCP fragmentation and
coalescing, rejects invalid UTF-8, and enforces the maximum encoded line size in both receive and
send paths. Usernames use a constrained, documented character set.

### `chatapp.server`

`ChatServer` owns the listening socket, username registry, shutdown event, and worker threads.
Registry access is protected by an `RLock`; blocking socket sends happen outside the registry
critical section.

Each accepted connection receives a daemon worker thread. The first protocol line is the username;
later lines are chat messages. Duplicate names are rejected atomically.

### `chatapp.client`

`ChatClient` owns one TCP connection and exposes connect/send/receive/close operations. The
terminal client runs receipt in a background thread so incoming messages do not corrupt the active
prompt.

### `chatapp.web`

The FastAPI gateway serves the static frontend and exposes `/ws`. Each accepted browser WebSocket
creates an ordinary `ChatClient` connected to `ChatServer`.

Two asynchronous forwarding tasks bridge WebSocket payloads and the blocking TCP client. Blocking
socket calls execute through `asyncio.to_thread()`, keeping the ASGI event loop responsive.

The gateway also serves `/healthz` and applies browser-oriented response security headers.

### `chatapp.app`

The combined launcher starts `ChatServer` in a background thread, then runs the web gateway with
Uvicorn. It is the easiest local product entry point and shuts down the TCP server when the web
process exits.

### `chatapp.admin`

The admin console delegates lifecycle operations to `ChatServer` instead of directly mutating
socket dictionaries. Commands are `list`, `kick <username>`, `help`, and `exit`.

## Concurrency model

The TCP backend uses one accept loop plus one worker thread per connected client. The web layer uses
ASGI tasks for WebSocket I/O and moves blocking `ChatClient` operations to worker threads.

For a substantially larger deployment, the clean next step would be an event-driven backend rather
than increasing thread coordination.

## TCP protocol

Every TCP frame is one UTF-8 line:

```text
<username>\n          # first client -> server line
<message>\n           # subsequent client -> server lines
<rendered message>\n  # server -> client
```

The protocol currently has no authentication, encryption, persistence, rooms, or delivery
acknowledgements.

## Browser gateway protocol

Browser messages use small JSON envelopes over WebSocket:

```json
{"type": "message", "text": "hello"}
```

Server envelopes use `connected`, `message`, `system`, `error`, and `disconnected` types.
See [WEB_FRONTEND.md](WEB_FRONTEND.md) for the complete contract.

## Product boundaries

The current application is deliberately a single-room, unauthenticated chat system. The browser UI
improves usability without pretending those missing security/product features already exist.
