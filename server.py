"""Compatibility launcher for the packaged ChatApp server."""

from chatapp.server import ChatServer, main

__all__ = ["ChatServer", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
