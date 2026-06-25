"""Memory tests — session + message round-trip against Postgres."""

from memory import short_term


def test_session_and_message_roundtrip():
    session_id = short_term.create_session(user_id="user:test", topic="pytest")
    short_term.append_message(session_id, "user", "hello from a test")
    short_term.append_message(session_id, "assistant", "hi back")

    msgs = short_term.get_recent_messages(session_id, limit=10)
    roles = [m.role for m in msgs]
    contents = [m.content for m in msgs]

    assert "user" in roles and "assistant" in roles
    assert "hello from a test" in contents
    # Oldest -> newest ordering
    assert contents.index("hello from a test") < contents.index("hi back")
