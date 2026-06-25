"""Episodic memory: runs + events.

Tracks what happened in each run so you can debug, replay, and analyze.
"""

import uuid
from typing import Any, Dict, List, Optional

from memory.db import as_jsonb, get_cursor, to_dict
from memory.models import Event, Run


def start_run(session_id: Optional[str], orchestrator: str,
              metadata: Optional[Dict[str, Any]] = None,
              tenant_id: Optional[str] = None) -> str:
    """Create a run record (status 'running', tagged with tenant) and return its UUID."""
    run_id = str(uuid.uuid4())
    with get_cursor(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            INSERT INTO runs (id, session_id, orchestrator, status, metadata, tenant_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (run_id, session_id, orchestrator, "running", as_jsonb(metadata), tenant_id),
        )
    return run_id


def finish_run(run_id: str, status: str = "success",
               error: Optional[str] = None) -> None:
    """Mark a run as finished with a final status."""
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE runs
            SET status = %s, error = %s
            WHERE id = %s
            """,
            (status, error, run_id),
        )


def log_event(run_id: str,
              event_type: str,
              message: str,
              agent_name: Optional[str] = None,
              payload: Optional[Dict[str, Any]] = None) -> None:
    """Append an event to a run's timeline."""
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO events (run_id, agent_name, event_type, message, payload)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, agent_name, event_type, message, as_jsonb(payload)),
        )


def get_events(run_id: str) -> List[Event]:
    """Fetch all events for a run, ordered oldest -> newest (for replay)."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, run_id, created_at, agent_name, event_type, message, payload
            FROM events
            WHERE run_id = %s
            ORDER BY created_at ASC
            """,
            (run_id,),
        )
        rows = cur.fetchall()
    return [
        Event(
            id=row[0],
            run_id=str(row[1]),
            created_at=row[2],
            agent_name=row[3],
            event_type=row[4],
            message=row[5],
            payload=to_dict(row[6]),
        )
        for row in rows
    ]
