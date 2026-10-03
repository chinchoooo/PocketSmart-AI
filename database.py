"""SQLite persistence for users and saved recommendations.

Uses only the standard library. A new short-lived connection is opened per call,
which keeps the code thread-safe under FastAPI's worker threadpool.
"""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username        TEXT PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    full_name       TEXT,
    hashed_password TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recommendations (
    id          TEXT PRIMARY KEY,
    username    TEXT NOT NULL REFERENCES users(username),
    rec_type    TEXT NOT NULL CHECK (rec_type IN ('home', 'party', 'jewelry')),
    created_at  TEXT NOT NULL,
    input_json  TEXT NOT NULL,
    result_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rec_user_time ON recommendations (username, created_at DESC);
"""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)


# --------------------------------- users --------------------------------------
def create_user(username: str, email: str, full_name: Optional[str], hashed_password: str) -> None:
    """Insert a user; raises ValueError if the username or email is taken."""
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                (username, email.lower(), full_name, hashed_password, _now()),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("Username or email already registered") from exc


def get_user(username: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return dict(row) if row else None


# ----------------------------- recommendations --------------------------------
def save_to_history(username: str, recommendation_type: str, input_data: Dict[str, Any],
                    result: Dict[str, Any]) -> str:
    """Persist one generated plan and return its id."""
    rec_id = uuid.uuid4().hex
    with _connect() as conn:
        conn.execute(
            "INSERT INTO recommendations VALUES (?, ?, ?, ?, ?, ?)",
            (rec_id, username, recommendation_type, _now(),
             json.dumps(input_data, default=str), json.dumps(result)),
        )
    return rec_id


def list_history(username: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Newest-first list of a user's saved plans."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM recommendations WHERE username = ? ORDER BY created_at DESC LIMIT ?",
            (username, limit),
        ).fetchall()
    return [_row_to_record(r) for r in rows]


def get_recommendation(username: str, rec_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM recommendations WHERE id = ? AND username = ?", (rec_id, username)
        ).fetchone()
    return _row_to_record(row) if row else None


def _row_to_record(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "timestamp": row["created_at"],
        "type": row["rec_type"],
        "input": json.loads(row["input_json"]),
        "full_result": json.loads(row["result_json"]),
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
