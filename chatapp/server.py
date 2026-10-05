"""Threaded TCP chat server."""

from __future__ import annotations

import argparse
import socket
import threading
from collections.abc import Callable

from prompt_toolkit import print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout

from chatapp.admin import ServerAdminHandler
from chatapp.protocol import LineBuffer, ProtocolError, encode_line, validate_username

Logger = Callable[[str], None]


class ChatServer:
    """Small threaded chat server with an encapsulated, lock-protected client registry."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        *,
        backlog: int = 32,
        recv_size: int = 4096,
        logger: Logger | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.backlog = backlog
        self.recv_size = recv_size
        self._logger = logger or (lambda message: print(message, flush=True))

        self._clients: dict[str, socket.socket] = {}
        self._clients_lock = threading.RLock()
        self._stop_event = threading.Event()
        self._listen_socket: socket.socket | None = None

    @property
    def address(self) -> tuple[str, int]:
        if self._listen_socket is None:
            return self.host, self.port
        host, port = self._listen_socket.getsockname()[:2]
        return str(host), int(port)

    def start(self) -> None:
        """Bind and start listening. Safe to call once before serve_forever()."""
        if self._listen_socket is not None:
            raise RuntimeError("server is already started")

        listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind((self.host, self.port))
        listen_socket.listen(self.backlog)
        listen_socket.settimeout(0.25)

        self._stop_event.clear()
        self._listen_socket = listen_socket
        self._logger(f"Server listening on {self.address[0]}:{self.address[1]}")

    def serve_forever(self) -> None:
        """Accept clients until shutdown() is requested."""
        if self._listen_socket is None:
            self.start()

        while not self._stop_event.is_set():
            listen_socket = self._listen_socket
            if listen_socket is None:
                break

            try:
                client_socket, client_address = listen_socket.accept()
            except TimeoutError:
                continue
            except OSError:
                if self._stop_event.is_set():
                    break
                raise

            thread = threading.Thread(
                target=self._handle_client,
                args=(client_socket, client_address),
                daemon=True,
                name=f"chat-client-{client_address[0]}:{client_address[1]}",
            )
            thread.start()

    def shutdown(self) -> None:
        """Stop accepting connections and close every connected client."""
        self._stop_event.set()

        listen_socket = self._listen_socket
        self._listen_socket = None
        if listen_socket is not None:
            try:
                listen_socket.close()
            except OSError:
                pass

        with self._clients_lock:
            clients = list(self._clients.items())
            self._clients.clear()

        for _, client_socket in clients:
            self._safe_send(client_socket, "[Server] Server is shutting down. Goodbye!")
            self._close_socket(client_socket)

        self._logger("Server shutdown complete")

    def connected_users(self) -> tuple[str, ...]:
        """Return a stable snapshot of connected usernames."""
        with self._clients_lock:
            return tuple(sorted(self._clients))

    def kick_user(self, username: str) -> bool:
        """Disconnect a named user. Return False when the user is not connected."""
        with self._clients_lock:
            client_socket = self._clients.pop(username, None)

        if client_socket is None:
            return False

        self._safe_send(client_socket, "[Server] You have been kicked from the server.")
        self._close_socket(client_socket)
        self.broadcast(f"[Server] User '{username}' has been kicked.")
        self._logger(f"Kicked user '{username}'")
        return True

    def broadcast(self, message: str, *, exclude: socket.socket | None = None) -> None:
        """Send one message to all currently registered clients."""
        with self._clients_lock:
            clients = list(self._clients.values())

        for client_socket in clients:
            if client_socket is exclude:
                continue
            self._safe_send(client_socket, message)

    def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
        receiver = LineBuffer()
        username: str | None = None
        registered = False

        try:
            pending_messages: list[str] = []
            while not pending_messages:
                data = client_socket.recv(self.recv_size)
                if not data:
                    return
                pending_messages.extend(receiver.feed(data))

            username = validate_username(pending_messages.pop(0))
            registered = self._register_client(username, client_socket)
            if not registered:
                self._safe_send(
                    client_socket,
                    "[Server] That username is already in use. Choose another name.",
                )
                return

            self._logger(f"{username} connected from {client_address}")
            self.broadcast(f"[Server] {username} has joined the chat.", exclude=client_socket)

            for message in pending_messages:
                self._handle_message(username, message, client_socket)

            while not self._stop_event.is_set():
                data = client_socket.recv(self.recv_size)
                if not data:
                    break
                for message in receiver.feed(data):
                    self._handle_message(username, message, client_socket)
        except ProtocolError as exc:
            self._safe_send(client_socket, f"[Server] Protocol error: {exc}")
            self._logger(f"Protocol error from {client_address}: {exc}")
        except (ConnectionResetError, BrokenPipeError, OSError) as exc:
            if not self._stop_event.is_set():
                self._logger(f"Connection error for {client_address}: {exc}")
        finally:
            if username is not None and registered and self._unregister_client(
                username, client_socket
            ):
                self.broadcast(f"[Server] {username} has left the chat.")
                self._logger(f"{username} disconnected")
            self._close_socket(client_socket)

    def _handle_message(
        self,
        username: str,
        message: str,
        sender_socket: socket.socket,
    ) -> None:
        message = message.strip()
        if not message:
            return
        self._logger(f"{username}: {message}")
        self.broadcast(f"{username}: {message}", exclude=sender_socket)

    def _register_client(self, username: str, client_socket: socket.socket) -> bool:
        with self._clients_lock:
            if username in self._clients:
                return False
            self._clients[username] = client_socket
            return True

    def _unregister_client(self, username: str, client_socket: socket.socket) -> bool:
        with self._clients_lock:
            if self._clients.get(username) is not client_socket:
                return False
            del self._clients[username]
            return True

    @staticmethod
    def _safe_send(client_socket: socket.socket, message: str) -> bool:
        try:
            client_socket.sendall(encode_line(message))
            return True
        except (BrokenPipeError, ConnectionResetError, OSError):
            return False

    @staticmethod
    def _close_socket(client_socket: socket.socket) -> None:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client_socket.close()
        except OSError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the ChatApp TCP server")
    parser.add_argument("--host", default="127.0.0.1", help="interface to bind")
    parser.add_argument("--port", type=int, default=8000, help="TCP port to bind")
    parser.add_argument(
        "--no-admin",
        action="store_true",
        help="disable the interactive admin console",
    )
    args = parser.parse_args(argv)

    def admin_print(message: str) -> None:
        with patch_stdout(raw=True):
            print_formatted_text(message)

    server = ChatServer(args.host, args.port, logger=admin_print)

    try:
        server.start()

        if not args.no_admin:
            admin_handler = ServerAdminHandler(server, output=admin_print)
            admin_thread = threading.Thread(
                target=admin_handler.handle_admin_commands,
                daemon=True,
                name="chat-admin",
            )
            admin_thread.start()

        server.serve_forever()
    except KeyboardInterrupt:
        admin_print("Server interrupted; shutting down.")
    except OSError as exc:
        admin_print(f"Server failed: {exc}")
        return 1
    finally:
        server.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
