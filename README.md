# ChatApp

ChatApp is a real-time Python chat application with a threaded TCP backend, terminal client, and a
responsive browser frontend. The browser experience is not a separate demo: its WebSocket gateway
bridges each browser session into the same TCP server used by command-line clients.

## What it looks like now

The default product experience is the web UI:

- polished dark responsive interface for desktop and mobile
- live WebSocket delivery
- shared room with terminal clients
- username validation and duplicate-name enforcement
- join/leave and server-event presentation
- connection-state feedback and graceful disconnect behavior
- no browser framework, CDN, or external asset dependency

Underneath the UI, ChatApp keeps a deliberately small networking architecture that is easy to
inspect and test.

## Quick start

ChatApp requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

### Start the complete product

```bash
chatapp-app
```

Then open:

```text
http://127.0.0.1:8080
```

This one command starts:

- the ChatApp TCP server on `127.0.0.1:8000`
- the browser/WebSocket gateway on `127.0.0.1:8080`

### Add a terminal client

In another terminal:

```bash
chatapp-client --name terminal-user
```

Messages from the terminal appear in the browser, and browser messages appear in the terminal.

## Run components separately

TCP server only:

```bash
chatapp-server
```

Browser gateway connected to an existing TCP server:

```bash
chatapp-web --chat-host 127.0.0.1 --chat-port 8000
```

Terminal client:

```bash
chatapp-client --name alice
```

The historical launchers remain valid:

```bash
python server.py
python client.py
```

## Architecture

```text
┌──────────────────────┐
│ Browser frontend     │
│ HTML · CSS · JS      │
└──────────┬───────────┘
           │ WebSocket
           ▼
┌──────────────────────┐
│ FastAPI web gateway  │
└──────────┬───────────┘
           │ ChatClient / TCP
           ▼
┌──────────────────────┐
│ ChatServer           │
│ username registry    │
│ broadcast + admin    │
└───────┬────────┬─────┘
        │        │
        ▼        ▼
 terminal    terminal
 client      client
```

The TCP server remains the source of truth. Browser connections do not maintain a second user
registry or separate chat room.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the complete networking design and
[docs/WEB_FRONTEND.md](docs/WEB_FRONTEND.md) for the browser gateway contract.

## Server admin console

When running `chatapp-server` directly, the interactive admin console supports:

| Command | Action |
| --- | --- |
| `list` | Show connected usernames |
| `kick <username>` | Disconnect one user |
| `help` | Show available commands |
| `exit` | Shut down the server and connected clients |

Usernames are 1–32 characters and may contain letters, numbers, `.`, `_`, and `-`.

## Development and QA

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the same quality gate as CI:

```bash
ruff check .
pytest
python -m build
```

The test suite covers:

- newline protocol fragmentation and validation
- admin command behavior
- TCP connection lifecycle and duplicate usernames
- browser/static asset serving
- WebSocket validation
- a real browser-gateway-to-TCP integration path

The integration test starts a real TCP server on an ephemeral port, opens a WebSocket browser
session, adds a raw TCP client, and verifies messages cross both transports.

## CI/CD

Pull requests run linting, tests, and package builds on Python 3.11, 3.12, and 3.13. Superseded PR
runs are cancelled automatically. Version tags build distribution artifacts and create GitHub
releases.

Dependabot monitors both Python packages and GitHub Actions dependencies.

## Project structure

```text
chatapp/
  app.py             combined product launcher
  admin.py           server administration commands
  client.py          reusable TCP client + terminal UI
  protocol.py        UTF-8 line framing and validation
  server.py          threaded TCP server
  web.py             FastAPI WebSocket/TCP gateway
  frontend/
    index.html       browser application shell
    styles.css       responsive visual system
    app.js           WebSocket UI behavior

tests/
  test_admin.py
  test_protocol.py
  test_server_integration.py
  test_web.py

docs/
  ARCHITECTURE.md
  WEB_FRONTEND.md
```

## Security boundaries

ChatApp remains a learning-scale networking application. The TCP transport is plaintext and there
is no authentication or end-to-end encryption. The web gateway adds browser security headers but
does not change those trust assumptions. Do not expose the application to an untrusted public
network or use it for sensitive data.

See [SECURITY.md](SECURITY.md).

## Roadmap

Strong next increments are authenticated identity, persisted history, rooms, TLS, structured
versioned protocol frames, moderation controls, and eventually an event-driven server for larger
connection counts.
