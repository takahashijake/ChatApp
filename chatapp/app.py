"""Combined ChatApp launcher for the TCP server and browser frontend."""

from __future__ import annotations

import argparse
import threading

import uvicorn

from chatapp.server import ChatServer
from chatapp.web import create_app


def _gateway_host(bind_host: str) -> str:
    if bind_host == "0.0.0.0":
        return "127.0.0.1"
    if bind_host == "::":
        return "::1"
    return bind_host


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the complete ChatApp product")
    parser.add_argument("--chat-host", default="127.0.0.1", help="TCP interface to bind")
    parser.add_argument("--chat-port", type=int, default=8000, help="TCP chat port")
    parser.add_argument("--web-host", default="127.0.0.1", help="web interface to bind")
    parser.add_argument("--web-port", type=int, default=8080, help="web frontend port")
    args = parser.parse_args(argv)

    server = ChatServer(args.chat_host, args.chat_port)
    try:
        server.start()
    except OSError as exc:
        print(f"Unable to start ChatApp TCP server: {exc}")
        return 1

    server_thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
        name="chatapp-tcp-server",
    )
    server_thread.start()

    backend_host = _gateway_host(server.address[0])
    app = create_app(backend_host, server.address[1])
    print(f"ChatApp web UI: http://{args.web_host}:{args.web_port}")

    try:
        uvicorn.run(app, host=args.web_host, port=args.web_port, log_level="info")
    finally:
        server.shutdown()
        server_thread.join(timeout=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
