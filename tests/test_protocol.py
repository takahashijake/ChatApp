import pytest

from chatapp.protocol import LineBuffer, ProtocolError, encode_line, validate_username


def test_line_buffer_handles_fragmented_and_multiple_messages() -> None:
    receiver = LineBuffer()

    assert receiver.feed(b"hel") == []
    assert receiver.feed(b"lo\nworld\npartial") == ["hello", "world"]
    assert receiver.has_pending_data
    assert receiver.feed(b" message\n") == ["partial message"]
    assert not receiver.has_pending_data


def test_line_buffer_rejects_invalid_utf8() -> None:
    receiver = LineBuffer()
    with pytest.raises(ProtocolError, match="valid UTF-8"):
        receiver.feed(b"\xff\n")


def test_line_buffer_rejects_oversized_message() -> None:
    receiver = LineBuffer(max_line_bytes=4)
    with pytest.raises(ProtocolError, match="maximum line size"):
        receiver.feed(b"12345")


@pytest.mark.parametrize("username", ["alice", "alice_2", "dev.user", "user-name"])
def test_validate_username_accepts_safe_names(username: str) -> None:
    assert validate_username(username) == username


@pytest.mark.parametrize("username", ["", " ", "two words", "name!", "x" * 33])
def test_validate_username_rejects_invalid_names(username: str) -> None:
    with pytest.raises(ProtocolError):
        validate_username(username)


def test_encode_line_rejects_embedded_newline() -> None:
    with pytest.raises(ProtocolError):
        encode_line("hello\nworld")
