# ChatApp

A small, testable TCP chat application built in Python. ChatApp provides a threaded multi-client
server, terminal client, and interactive server administration console while keeping the wire
protocol deliberately simple.

## Highlights

- Multi-client TCP chat with newline-delimited UTF-8 messages.
- Atomic username registration with duplicate-name rejection.
- Admin commands for listing users, kicking users, and shutting down cleanly.
- Graceful socket cleanup and explicit handling for normal disconnect failures.
- Installable command-line entry points plus backward-compatible top-level scripts.
- Automated protocol, admin, and real-socket integration tests.
- CI across Python 3.11-3.13, dependency updates, and tag-driven GitHub releases.

## Requirements

- Python 3.11+
- `prompt-toolkit` (installed automatically)

## Quick start

Create an environment and install the project:

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

Start the server:

```bash
chatapp-server
```

Then, in another terminal:

```bash
chatapp-client --name alice
```

The historical entry points continue to work:

```bash
python server.py
python client.py
```

By default the application uses `127.0.0.1:8000`. Both commands accept `--host` and `--port`.
Run `chatapp-server --no-admin` when an interactive server console is not appropriate.

## Server admin console

While the server is running with its admin console enabled:

| Command | Action |
| --- | --- |
| `list` | Show connected usernames |
| `kick <username>` | Disconnect one user |
| `help` | Show available commands |
| `exit` | Shut down the server and connected clients |

Usernames are 1-32 characters and may contain letters, numbers, `.`, `_`, and `-`.

## Development

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the quality gate:

```bash
ruff check .
pytest
python -m build
```

Apply formatting with:

```bash
ruff format .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contributor expectations and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the concurrency and protocol design.

## CI/CD

Pull requests run linting, tests, and package builds in GitHub Actions. Tests run on Python 3.11,
3.12, and 3.13. Pushing a tag such as `v0.1.0` builds wheel/source artifacts and creates a GitHub
release automatically.

Dependabot checks Python and GitHub Actions dependencies weekly.

## Security

This is a learning-scale chat application, not a production messaging service. Connections are
plaintext TCP and there is no authentication or end-to-end encryption. Do not expose it to an
untrusted public network or use it for sensitive data. See [SECURITY.md](SECURITY.md).

## Project structure

```text
chatapp/
  admin.py       server administration command parsing
  client.py      reusable client plus terminal UI
  protocol.py    framing and validation
  server.py      threaded server and client registry
tests/           unit and TCP integration tests
docs/            architecture documentation
.github/         CI/CD and repository automation
client.py        compatibility launcher
server.py        compatibility launcher
commands.py      compatibility import
```

## Roadmap

Good next product increments include chat rooms, authenticated identities, TLS, structured protocol
frames, persisted history, and an asynchronous server implementation. Each should be added with a
clear protocol versioning and migration story.
