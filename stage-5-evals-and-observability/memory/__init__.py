"""
Memory Service for Stage 3.

All agents and orchestrators talk to this package — never directly to the
Postgres tables. The three memory types are:

  - short_term : sessions + messages (per-session conversation history)
  - long_term  : memories (pgvector semantic search over brand/facts/insights)
  - episodic   : runs + events (timelines for debugging, replay, analytics)
"""

from memory import short_term, long_term, episodic

__all__ = ["short_term", "long_term", "episodic"]
