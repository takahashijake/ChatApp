"""Compatibility launcher for the packaged ChatApp client."""

from chatapp.client import ChatClient, main

__all__ = ["ChatClient", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
