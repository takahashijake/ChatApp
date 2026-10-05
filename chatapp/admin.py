"""Interactive administration commands for the ChatApp server."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from prompt_toolkit import PromptSession


class AdminServer(Protocol):
    def connected_users(self) -> tuple[str, ...]: ...

    def kick_user(self, username: str) -> bool: ...

    def shutdown(self) -> None: ...


class ServerAdminHandler:
    """Parse and execute the small set of supported server administration commands."""

    def __init__(
        self,
        server: AdminServer,
        *,
        output: Callable[[str], None] = print,
        session: PromptSession | None = None,
    ) -> None:
        self.server = server
        self.output = output
        self.session = session or PromptSession()

    def execute(self, command_line: str) -> bool:
        """Execute one command. Return False when the console should exit."""
        parts = command_line.strip().split()
        if not parts:
            return True

        action = parts[0].lower()

        if action == "list":
            users = self.server.connected_users()
            if users:
                self.output("Connected users: " + ", ".join(users))
            else:
                self.output("No users are currently connected.")
            return True

        if action == "kick":
            if len(parts) != 2:
                self.output("Usage: kick <username>")
                return True
            username = parts[1]
            if self.server.kick_user(username):
                self.output(f"Kicked user '{username}'.")
            else:
                self.output(f"User '{username}' not found.")
            return True

        if action in {"help", "?"}:
            self.output("Commands: list, kick <username>, help, exit")
            return True

        if action in {"exit", "quit"}:
            self.output("Shutting down server.")
            self.server.shutdown()
            return False

        self.output("Unknown command. Commands: list, kick <username>, help, exit")
        return True

    def handle_admin_commands(self) -> None:
        """Run the interactive admin loop."""
        while True:
            try:
                command_line = self.session.prompt("Admin > ")
            except (EOFError, KeyboardInterrupt):
                self.output("Admin console closed.")
                return
            if not self.execute(command_line):
                return
