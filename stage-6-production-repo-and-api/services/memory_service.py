"""Thin façade over the memory module (short-term, long-term, episodic)."""

from typing import Any, Dict, List, Optional, Tuple

from memory import short_term, long_term, episodic
from memory.models import Message, MemoryRecord


def recent_messages(session_id: str, limit: int = 20) -> List[Message]:
    return short_term.get_recent_messages(session_id, limit=limit)


def remember(kind: str, label: str, content: str,
             session_id: Optional[str] = None,
             user_id: Optional[str] = None) -> int:
    """Store a long-term semantic memory and return its id."""
    return long_term.add_memory(
        kind=kind, label=label, content=content,
        session_id=session_id, user_id=user_id,
    )


def search(query: str, kind: Optional[str] = None,
           user_id: Optional[str] = None,
           limit: int = 5) -> List[Tuple[MemoryRecord, float]]:
    """Semantic search over long-term memory (pgvector)."""
    return long_term.search_memory(query, user_id=user_id, kind=kind, limit=limit)


def run_events(run_id: str) -> List[Dict[str, Any]]:
    """Episodic event timeline for a run (for replay/debugging)."""
    return [
        {
            "created_at": e.created_at,
            "event_type": e.event_type,
            "agent_name": e.agent_name,
            "message": e.message,
        }
        for e in episodic.get_events(run_id)
    ]
