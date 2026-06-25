"""Long-term semantic memory (pgvector).

Stores facts, brand rules, and reusable knowledge as embeddings in Postgres,
and retrieves them with cosine-distance similarity search.
"""

from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from config import OPENAI_API_KEY
from memory.db import as_jsonb, get_cursor, to_dict
from memory.models import MemoryRecord

client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 1536  # must match vector(1536) in the migration


def _embed(text: str) -> List[float]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIM,
    )
    return response.data[0].embedding


def _to_pgvector(embedding: List[float]) -> str:
    """Format a float list as pgvector's text literal: '[0.1,0.2,...]'."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def add_memory(kind: str,
               label: str,
               content: str,
               session_id: Optional[str] = None,
               user_id: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None) -> int:
    """Insert a new long-term memory and return its ID."""
    embedding = _embed(content)
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO memories
                (session_id, user_id, kind, label, content, metadata, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
            RETURNING id
            """,
            (
                session_id,
                user_id,
                kind,
                label,
                content,
                as_jsonb(metadata),
                _to_pgvector(embedding),
            ),
        )
        mem_id = cur.fetchone()[0]
    return mem_id


def search_memory(query: str,
                  user_id: Optional[str] = None,
                  kind: Optional[str] = None,
                  limit: int = 5) -> List[Tuple[MemoryRecord, float]]:
    """Semantic search over memories using cosine distance (lower is closer)."""
    query_embedding = _to_pgvector(_embed(query))
    base = (
        "SELECT id, created_at, session_id, user_id, kind, label, content, "
        "metadata, embedding, embedding <=> %s::vector AS distance "
        "FROM memories"
    )
    params: List[Any] = [query_embedding]
    conditions: List[str] = []

    if user_id:
        conditions.append("user_id = %s")
        params.append(user_id)
    if kind:
        conditions.append("kind = %s")
        params.append(kind)

    if conditions:
        base += " WHERE " + " AND ".join(conditions)
    base += " ORDER BY distance ASC LIMIT %s"
    params.append(limit)

    with get_cursor() as cur:
        cur.execute(base, params)
        rows = cur.fetchall()

    results: List[Tuple[MemoryRecord, float]] = []
    for row in rows:
        record = MemoryRecord(
            id=row[0],
            created_at=row[1],
            session_id=str(row[2]) if row[2] else None,
            user_id=row[3],
            kind=row[4],
            label=row[5],
            content=row[6],
            metadata=to_dict(row[7]),
            embedding=[],  # raw vector omitted from results to keep them light
        )
        distance = float(row[9])
        results.append((record, distance))
    return results
