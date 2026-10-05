# Web frontend

ChatApp includes a browser-native UI without replacing its TCP architecture.

## How it fits

Browsers cannot open arbitrary TCP sockets, so the web layer is intentionally a transport gateway:

```text
Browser UI
   │
   │ WebSocket
   ▼
FastAPI gateway
   │
   │ ChatClient
   ▼
ChatApp TCP server
   │
   ├── terminal client
   ├── terminal client
   └── browser-backed client
```

Every browser session receives its own ordinary `ChatClient`. That means terminal and browser
users share the same username registry, join/leave events, admin kicks, broadcasts, and shutdown
behavior.

## Entry points

### Complete product

```bash
chatapp-app
```

Starts the TCP server on `127.0.0.1:8000` and the web UI on `127.0.0.1:8080`.

### Gateway only

```bash
chatapp-web --chat-host 127.0.0.1 --chat-port 8000
```

Use this when a ChatApp TCP server is already running elsewhere.

## WebSocket contract

The browser connects to:

```text
/ws?name=<username>
```

Browser-to-gateway payload:

```json
{"type": "message", "text": "hello"}
```

Gateway-to-browser payloads include:

```json
{"type": "connected", "name": "alice"}
{"type": "message", "text": "bob: hello"}
{"type": "system", "text": "[Server] bob has joined the chat."}
{"type": "error", "message": "..."}
{"type": "disconnected", "message": "..."}
```

## Frontend behavior

- Responsive desktop/mobile layout.
- Username validation before opening the backend connection.
- Optimistic rendering for the sender's own messages.
- Distinct chat and system-event presentation.
- Connection-state indicator and disconnect handling.
- No third-party browser dependencies or external asset/CDN requirements.
- Security headers are applied to HTTP responses.

The web layer intentionally does not add a second chat-state implementation. The TCP server remains
the source of truth.
