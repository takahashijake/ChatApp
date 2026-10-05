from __future__ import annotations

import socket
import threading
import time
from collections.abc import Callable

from fastapi.testclient import TestClient

from chatapp.server import ChatServer
from chatapp.web import create_app


def wait_for(predicate: Callable[[], bool], timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition was not met before timeout")


def start_test_server() -> tuple[ChatServer, threading.Thread]:
    server = ChatServer("127.0.0.1", 0, logger=lambda _: None)
    server.start()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_frontend_and_health_endpoint_are_served() -> None:
    client = TestClient(create_app("127.0.0.1", 8000))

    response = client.get("/")
    assert response.status_code == 200
    assert "Real-time chat, without the terminal." in response.text
    assert response.headers["x-frame-options"] == "DENY"

    stylesheet = client.get("/static/styles.css")
    assert stylesheet.status_code == 200
    assert "--accent:" in stylesheet.text

    health = client.get("/healthz")
    assert health.json() == {
        "status": "ok",
        "chat_host": "127.0.0.1",
        "chat_port": 8000,
    }


def test_websocket_rejects_invalid_username_before_backend_connect() -> None:
    client = TestClient(create_app("127.0.0.1", 65534))

    with client.websocket_connect("/ws?name=two%20words") as websocket:
        payload = websocket.receive_json()
        assert payload["type"] == "error"
        assert "username must be" in payload["message"]


def test_websocket_bridges_browser_and_tcp_clients() -> None:
    server, server_thread = start_test_server()
    app = create_app(*server.address)
    browser = TestClient(app)
    bob = socket.create_connection(server.address, timeout=1)
    bob.settimeout(1)

    try:
        with browser.websocket_connect("/ws?name=alice") as websocket:
            connected = websocket.receive_json()
            assert connected == {"type": "connected", "name": "alice"}
            wait_for(lambda: "alice" in server.connected_users())

            bob.sendall(b"bob\n")
            wait_for(lambda: server.connected_users() == ("alice", "bob"))

            join_event = websocket.receive_json()
            assert join_event["type"] == "system"
            assert "bob has joined" in join_event["text"]

            bob.sendall(b"hello from tcp\n")
            inbound = websocket.receive_json()
            assert inbound == {"type": "message", "text": "bob: hello from tcp"}

            websocket.send_json({"type": "message", "text": "hello from browser"})
            received_by_bob = bob.recv(4096).decode()
            assert "alice: hello from browser" in received_by_bob
    finally:
        bob.close()
        server.shutdown()
        server_thread.join(timeout=2)

    assert not server_thread.is_alive()
