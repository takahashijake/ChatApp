from __future__ import annotations

import socket
import threading
import time
from collections.abc import Callable

from chatapp.server import ChatServer


def wait_for(predicate: Callable[[], bool], timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition was not met before timeout")


def recv_until(client: socket.socket, needle: str, max_reads: int = 4) -> str:
    chunks = ""
    for _ in range(max_reads):
        chunks += client.recv(4096).decode()
        if needle.lower() in chunks.lower():
            return chunks
    raise AssertionError(f"did not receive expected text: {needle}")


def start_test_server() -> tuple[ChatServer, threading.Thread]:
    server = ChatServer("127.0.0.1", 0, logger=lambda _: None)
    server.start()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_client_can_register_and_be_kicked() -> None:
    server, thread = start_test_server()
    client = socket.create_connection(server.address, timeout=1)
    client.settimeout(1)

    try:
        client.sendall(b"alice\n")
        wait_for(lambda: server.connected_users() == ("alice",))
        welcome = recv_until(client, "welcome")
        assert "alice" in welcome.lower()

        assert server.kick_user("alice")
        payload = recv_until(client, "kicked")
        assert "kicked" in payload.lower()
        wait_for(lambda: server.connected_users() == ())
    finally:
        client.close()
        server.shutdown()
        thread.join(timeout=2)

    assert not thread.is_alive()


def test_duplicate_usernames_are_rejected() -> None:
    server, thread = start_test_server()
    first = socket.create_connection(server.address, timeout=1)
    duplicate = socket.create_connection(server.address, timeout=1)
    duplicate.settimeout(1)

    try:
        first.sendall(b"alice\n")
        wait_for(lambda: server.connected_users() == ("alice",))
        assert "welcome" in recv_until(first, "welcome").lower()

        duplicate.sendall(b"alice\n")
        response = recv_until(duplicate, "already in use")
        assert "already in use" in response
        assert server.connected_users() == ("alice",)
    finally:
        first.close()
        duplicate.close()
        server.shutdown()
        thread.join(timeout=2)

    assert not thread.is_alive()
