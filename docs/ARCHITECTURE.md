# Architecture

ChatApp is intentionally small, but the implementation separates networking, protocol parsing,
administration, and terminal UI so each piece can be tested independently.

## Components

### `chatapp.protocol`

Defines the newline-delimited UTF-8 wire format. `LineBuffer` handles TCP fragmentation and
coalescing, enforces a maximum line size, and rejects invalid UTF-8. Usernames are constrained to
a small, documented character set.

### `chatapp.server`

`ChatServer` owns the listening socket, client registry, shutdown event, and worker threads.
Registry access is protected by an `RLock`; potentially blocking socket sends happen outside the
registry critical section.

Each accepted connection gets a daemon worker thread. The first protocol line is the username;
subsequent lines are chat messages. Duplicate names are rejected atomically.

### `chatapp.client`

`ChatClient` owns a single TCP connection and exposes connect/send/receive/close operations.
The interactive CLI runs message receipt in a background thread so incoming messages do not corrupt
the user's active prompt.

### `chatapp.admin`

The admin console delegates lifecycle operations to `ChatServer` instead of mutating shared
dictionaries directly. Supported commands are `list`, `kick <username>`, `help`, and `exit`.

## Concurrency model

The server uses one accept loop plus one worker thread per connected client. This is appropriate for
a learning-scale chat application. The client registry is the only shared mutable server state.

For a significantly larger deployment, the next architectural step would be an event-driven design
using `asyncio` or a dedicated networking framework rather than adding more thread coordination.

## Protocol

Every frame is one UTF-8 line:

```text
<username>\n          # first client -> server line
<message>\n           # subsequent client -> server lines
<rendered message>\n  # server -> client
```

The protocol currently has no authentication, encryption, persistence, rooms, or delivery
acknowledgements. Those are deliberate product boundaries, not implied guarantees.
