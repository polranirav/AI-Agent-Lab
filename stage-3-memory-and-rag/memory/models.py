"""Typed dataclasses for memory objects.

These make it easier to reason about what we store and return.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Session:
    id: str
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str]
    topic: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    id: int
    session_id: str
    created_at: datetime
    role: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryRecord:
    id: int
    created_at: datetime
    session_id: Optional[str]
    user_id: Optional[str]
    kind: str
    label: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: List[float] = field(default_factory=list)


@dataclass
class Run:
    id: str
    created_at: datetime
    session_id: Optional[str]
    orchestrator: str
    status: str
    error: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    id: int
    run_id: str
    created_at: datetime
    agent_name: Optional[str]
    event_type: str
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)
