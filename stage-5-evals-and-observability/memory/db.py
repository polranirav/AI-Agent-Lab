"""Central DB connection + helpers.

A thin layer that gives consistent connection/commit logic and is easy to
swap for a pooling library later (e.g. psycopg_pool) without touching callers.
"""

import json
from contextlib import contextmanager

import psycopg
from psycopg.types.json import Jsonb

from config import DATABASE_URL


@contextmanager
def get_conn():
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_cursor():
    with get_conn() as conn:
        with conn.cursor() as cur:
            yield cur
            conn.commit()


def as_jsonb(value) -> Jsonb:
    """Adapt a Python dict to a JSONB-bindable parameter for psycopg."""
    return Jsonb(value if value is not None else {})


def to_dict(value) -> dict:
    """Normalize a JSONB column read back from Postgres into a dict."""
    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    return value
