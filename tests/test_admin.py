from chatapp.admin import ServerAdminHandler


class FakeServer:
    def __init__(self) -> None:
        self.users = {"alice", "bob"}
        self.shutdown_called = False

    def connected_users(self) -> tuple[str, ...]:
        return tuple(sorted(self.users))

    def kick_user(self, username: str) -> bool:
        if username not in self.users:
            return False
        self.users.remove(username)
        return True

    def shutdown(self) -> None:
        self.shutdown_called = True


def test_admin_list_and_kick_commands() -> None:
    server = FakeServer()
    output: list[str] = []
    handler = ServerAdminHandler(server, output=output.append)

    assert handler.execute("list")
    assert output[-1] == "Connected users: alice, bob"

    assert handler.execute("kick alice")
    assert "alice" not in server.users
    assert output[-1] == "Kicked user 'alice'."


def test_admin_exit_requests_server_shutdown() -> None:
    server = FakeServer()
    handler = ServerAdminHandler(server, output=lambda _: None)

    assert not handler.execute("exit")
    assert server.shutdown_called
