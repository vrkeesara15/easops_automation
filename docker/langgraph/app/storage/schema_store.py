"""Simple SQLite-backed storage for agent run schemas.

This module persists agent run input/output schemas to a local SQLite database
located at ``/data/agent_runs.db``. It does not rely on migrations or an ORM so
it can run in constrained environments such as Cloud Run with a mounted volume.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


DB_PATH = Path("/data/agent_runs.db")
_table_initialized = False
_lock = threading.RLock()


@dataclass(frozen=True)
class AgentRunRecord:
    """Convenience structure for agent run data."""

    run_id: str
    agent_id: str
    agent_version: str
    input_schema: str
    output_schema: str
    metadata: Optional[str]
    created_at: datetime


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    """Initialize the SQLite database and ensure the agent_runs table exists."""
    global _table_initialized
    with _lock:
        if _table_initialized:
            return
        with _get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_runs (
                    run_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    agent_version TEXT,
                    input_schema TEXT,
                    output_schema TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP
                )
                """
            )
        _table_initialized = True


def _serialize_json(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    return json.dumps(value, separators=(",", ":"))


def save_run(
    run_id: str,
    agent_id: str,
    agent_version: str,
    input_schema: Any,
    output_schema: Any,
    metadata: Optional[Any] = None,
    created_at: Optional[datetime] = None,
) -> None:
    """Persist a run record.

    JSON fields are serialized to text before insertion. ``created_at``
    defaults to the current UTC time when omitted.
    """

    init_db()
    created_at = created_at or datetime.now(timezone.utc)
    created_at_str = created_at.isoformat()

    input_json = _serialize_json(input_schema)
    output_json = _serialize_json(output_schema)
    metadata_json = _serialize_json(metadata) if metadata is not None else None

    with _lock:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_runs (
                    run_id, agent_id, agent_version, input_schema, output_schema, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    agent_id,
                    agent_version,
                    input_json,
                    output_json,
                    metadata_json,
                    created_at_str,
                ),
            )


def _row_to_record(row: sqlite3.Row) -> AgentRunRecord:
    created_at = row["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    return AgentRunRecord(
        run_id=row["run_id"],
        agent_id=row["agent_id"],
        agent_version=row["agent_version"],
        input_schema=row["input_schema"],
        output_schema=row["output_schema"],
        metadata=row["metadata"],
        created_at=created_at,
    )


def get_run(run_id: str) -> Optional[AgentRunRecord]:
    """Retrieve a specific run by id."""

    init_db()
    with _lock:
        with _get_connection() as conn:
            cursor = conn.execute("SELECT * FROM agent_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            return _row_to_record(row) if row else None


def list_runs(agent_id: Optional[str] = None) -> Iterable[AgentRunRecord]:
    """List runs, optionally filtered by agent id."""

    init_db()
    query = "SELECT * FROM agent_runs"
    params: tuple[Any, ...] = ()
    if agent_id:
        query += " WHERE agent_id = ?"
        params = (agent_id,)
    query += " ORDER BY created_at DESC"

    with _lock:
        with _get_connection() as conn:
            cursor = conn.execute(query, params)
            for row in cursor.fetchall():
                yield _row_to_record(row)


# Usage example from an agent execution
if __name__ == "__main__":
    run_input = {"action": "search", "query": "best pizza"}
    run_output = {"result": "pepperoni"}

    save_run(
        run_id="run-123",
        agent_id="pizza-agent",
        agent_version="1.0.0",
        input_schema=run_input,
        output_schema=run_output,
        metadata={"trigger": "manual"},
    )

    retrieved = get_run("run-123")
    print("Saved and retrieved run:", retrieved)

    print("All runs for pizza-agent:")
    for record in list_runs("pizza-agent"):
        print("-", record)
