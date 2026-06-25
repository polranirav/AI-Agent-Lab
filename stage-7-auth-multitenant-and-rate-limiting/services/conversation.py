"""Session orchestration helpers.

Centralizes the "open a session + run, then close the run" lifecycle so routes
and jobs don't repeat it. Used by the HTTP API.
"""

from typing import Optional, Tuple

from memory import short_term, episodic


def open_run(user_id: Optional[str], topic: str,
             orchestrator: str = "http-api") -> Tuple[str, str]:
    """Create a session + run and return (session_id, run_id)."""
    session_id = short_term.create_session(user_id=user_id, topic=topic)
    run_id = episodic.start_run(
        session_id, orchestrator=orchestrator, metadata={"topic": topic},
    )
    return session_id, run_id


def close_run(run_id: str, status: str = "success",
              error: Optional[str] = None) -> None:
    """Finish a run with a final status."""
    episodic.finish_run(run_id, status=status, error=error)
