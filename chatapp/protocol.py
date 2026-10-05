"""Line-oriented wire protocol helpers used by the ChatApp client and server."""

from __future__ import annotations

import re

MAX_LINE_BYTES = 64 * 1024
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")


class ProtocolError(ValueError):
    """Raised when a peer sends malformed or oversized protocol data."""


class LineBuffer:
    """Incrementally decode UTF-8, newline-delimited messages."""

    def __init__(self, max_line_bytes: int = MAX_LINE_BYTES) -> None:
        if max_line_bytes <= 0:
            raise ValueError("max_line_bytes must be positive")
        self._buffer = bytearray()
        self._max_line_bytes = max_line_bytes

    def feed(self, chunk: bytes) -> list[str]:
        """Append bytes and return every complete decoded line."""
        if not isinstance(chunk, bytes):
            raise TypeError("chunk must be bytes")

        self._buffer.extend(chunk)
        messages: list[str] = []

        while True:
            newline_index = self._buffer.find(b"\n")
            if newline_index < 0:
                if len(self._buffer) > self._max_line_bytes:
                    raise ProtocolError("message exceeds the maximum line size")
                break

            if newline_index > self._max_line_bytes:
                raise ProtocolError("message exceeds the maximum line size")

            raw_line = bytes(self._buffer[:newline_index])
            del self._buffer[: newline_index + 1]

            if raw_line.endswith(b"\r"):
                raw_line = raw_line[:-1]

            try:
                messages.append(raw_line.decode("utf-8"))
            except UnicodeDecodeError as exc:
                raise ProtocolError("message is not valid UTF-8") from exc

        return messages

    @property
    def has_pending_data(self) -> bool:
        return bool(self._buffer)


def encode_line(message: str) -> bytes:
    """Encode one protocol line, rejecting embedded newlines."""
    if "\n" in message or "\r" in message:
        raise ProtocolError("messages must not contain newline characters")
    return f"{message}\n".encode("utf-8")


def validate_username(username: str) -> str:
    """Return a normalized username or raise ProtocolError."""
    normalized = username.strip()
    if not _USERNAME_RE.fullmatch(normalized):
        raise ProtocolError(
            "username must be 1-32 characters using letters, numbers, '.', '_' or '-'"
        )
    return normalized
