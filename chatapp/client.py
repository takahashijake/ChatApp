"""Interactive TCP client for ChatApp."""

from __future__ import annotations

import argparse
import socket
import threading
from collections.abc import Iterator
from contextlib import suppress

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout

from chatapp.protocol import LineBuffer, ProtocolError, encode_line, validate_username


class ChatClient:
    """Thin client wrapper that separates socket behavior from terminal UI."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        self.host = host
        self.port = port
        self._socket: socket.socket | None = None
        self._connected = threading.Event()

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    def connect(self, username: str, *, timeout: float = 5.0) -> None:
        if self.is_connected:
            raise RuntimeError("client is already connected")

        username = validate_username(username)
        stream_socket = socket.create_connection((self.host, self.port), timeout=timeout)
        stream_socket.settimeout(None)

        try:
            stream_socket.sendall(encode_line(username))
        except Exception:
            stream_socket.close()
            raise

        self._socket = stream_socket
        self._connected.set()

    def send_message(self, message: str) -> None:
        stream_socket = self._socket
        if stream_socket is None or not self.is_connected:
            raise ConnectionError("client is not connected")

        normalized = message.strip()
        if not normalized:
            return
        stream_socket.sendall(encode_line(normalized))

    def receive_messages(self) -> Iterator[str]:
        stream_socket = self._socket
        if stream_socket is None or not self.is_connected:
            raise ConnectionError("client is not connected")

        receiver = LineBuffer()
        try:
            while self.is_connected:
                data = stream_socket.recv(4096)
                if not data:
                    return
                yield from receiver.feed(data)
        except OSError:
            return
        finally:
            self._connected.clear()

    def close(self) -> None:
        self._connected.clear()
        stream_socket = self._socket
        self._socket = None
        if stream_socket is None:
            return
        with suppress(OSError):
            stream_socket.shutdown(socket.SHUT_RDWR)
        stream_socket.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Connect to a ChatApp server")
    parser.add_argument("--host", default="127.0.0.1", help="server host")
    parser.add_argument("--port", type=int, default=8000, help="server TCP port")
    parser.add_argument("--name", help="username; prompts when omitted")
    args = parser.parse_args(argv)

    session = PromptSession()
    username = args.name or session.prompt("Name: ")

    client = ChatClient(args.host, args.port)
    try:
        client.connect(username)
    except (OSError, ProtocolError) as exc:
        print_formatted_text(f"Connection failed: {exc}")
        return 1

    def receive_loop() -> None:
        for message in client.receive_messages():
            with patch_stdout(raw=True):
                print_formatted_text(message)

    receive_thread = threading.Thread(target=receive_loop, daemon=True, name="chat-receiver")
    receive_thread.start()

    print_formatted_text("Connected. Type /quit to leave.")

    try:
        while client.is_connected:
            message = session.prompt("You: ")
            if message.strip().lower() in {"/quit", "/exit"}:
                break
            try:
                client.send_message(message)
            except (OSError, ProtocolError) as exc:
                print_formatted_text(f"Send failed: {exc}")
                break
    except (EOFError, KeyboardInterrupt):
        print_formatted_text("Client interrupted.")
    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
