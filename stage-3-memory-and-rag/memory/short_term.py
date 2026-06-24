"""Short-term memory: sessions + messages (per-session conversation history)."""

import uuid
from typing import Any, Dict, List, Optional

from memory.db import as_jsonb, get_cursor, to_dict
from memory.models import Message, Session


def create_session(user_id: Optional[str] = None,
                   topic: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
    """Create a new session and return its UUID string."""
    session_id = str(uuid.uuid4())
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO sessions (id, user_id, topic, metadata)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, user_id, topic, as_jsonb(metadata)),
        )
    return session_id


def get_session(session_id: str) -> Optional[Session]:
    """Fetch a single session by id, or None if it doesn't exist."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, created_at, updated_at, user_id, topic, metadata
            FROM sessions
            WHERE id = %s
            """,
            (session_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return Session(
        id=str(row[0]),
        created_at=row[1],
        updated_at=row[2],
        user_id=row[3],
        topic=row[4],
        metadata=to_dict(row[5]),
    )


def append_message(session_id: str, role: str, content: str,
                   metadata: Optional[Dict[str, Any]] = None) -> None:
    """Append a message to the short-term memory for this session."""
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO messages (session_id, role, content, metadata)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, role, content, as_jsonb(metadata)),
        )
        cur.execute(
            "UPDATE sessions SET updated_at = now() WHERE id = %s",
            (session_id,),
        )


def get_recent_messages(session_id: str, limit: int = 20) -> List[Message]:
    """Fetch recent messages for a session, ordered oldest -> newest."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, session_id, created_at, role, content, metadata
            FROM messages
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (session_id, limit),
        )
        rows = cur.fetchall()
    messages = [
        Message(
            id=row[0],
            session_id=str(row[1]),
            created_at=row[2],
            role=row[3],
            content=row[4],
            metadata=to_dict(row[5]),
        )
        for row in reversed(rows)  # reverse to oldest -> newest
    ]
    return messages


def summarize_history_text(messages: List[Message]) -> str:
    """Simple concatenation for now; replace with LLM summarization later."""
    parts = []
    for m in messages:
        if m.role == "user":
            prefix = "User"
        elif m.role == "assistant":
            prefix = "Assistant"
        else:
            prefix = m.role.capitalize()
        parts.append(f"[{prefix}] {m.content}")
    return "\n".join(parts)
