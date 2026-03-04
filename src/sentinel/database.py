"""SQLite database for Nyayo Sentinel signals."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import Signal

# Database lives next to the project root
_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
_DB_PATH = _DB_DIR / "sentinel.db"


def _get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row factory enabled."""
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent reads
    return conn


def init_db() -> None:
    """Create the signals table if it doesn't exist."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT,
            topic TEXT NOT NULL,
            tension_score REAL NOT NULL,
            county TEXT,
            supported BOOLEAN,
            language TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Indexes for common queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_topic ON signals(topic)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_county ON signals(county)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON signals(created_at)")
    conn.commit()
    conn.close()


def insert_signal(signal: Signal) -> int:
    """Insert a signal record. Returns the new row ID."""
    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO signals (question, answer, topic, tension_score, county, supported, language)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            signal.question,
            signal.answer,
            signal.topic,
            signal.tension_score,
            signal.county,
            signal.supported,
            signal.language,
        ),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_signals(
    limit: int = 50,
    offset: int = 0,
    topic: Optional[str] = None,
    county: Optional[str] = None,
    days: Optional[int] = None,
) -> list[dict]:
    """Query signals with optional filters."""
    conn = _get_connection()
    query = "SELECT * FROM signals WHERE 1=1"
    params: list = []

    if topic:
        query += " AND topic = ?"
        params.append(topic)
    if county:
        query += " AND county = ?"
        params.append(county)
    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query += " AND created_at >= ?"
        params.append(cutoff)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_by_topic(days: Optional[int] = None) -> list[dict]:
    """Count signals grouped by topic."""
    conn = _get_connection()
    query = "SELECT topic, COUNT(*) as count FROM signals"
    params: list = []

    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query += " WHERE created_at >= ?"
        params.append(cutoff)

    query += " GROUP BY topic ORDER BY count DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def county_tension(days: Optional[int] = None) -> list[dict]:
    """Average tension per county."""
    conn = _get_connection()
    query = """
        SELECT county, AVG(tension_score) as avg_tension, COUNT(*) as question_count
        FROM signals
        WHERE county IS NOT NULL
    """
    params: list = []

    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query += " AND created_at >= ?"
        params.append(cutoff)

    query += " GROUP BY county ORDER BY avg_tension DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def unanswered_questions(days: Optional[int] = None, limit: int = 10) -> dict:
    """Get no-answer stats and sample unanswered questions."""
    conn = _get_connection()
    base_where = "WHERE 1=1"
    params: list = []

    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        base_where += " AND created_at >= ?"
        params.append(cutoff)

    # Total count
    total = conn.execute(
        f"SELECT COUNT(*) FROM signals {base_where}", params
    ).fetchone()[0]

    # Unanswered count
    unanswered = conn.execute(
        f"SELECT COUNT(*) FROM signals {base_where} AND supported = 0", params
    ).fetchone()[0]

    # Sample unanswered questions
    samples = conn.execute(
        f"SELECT question FROM signals {base_where} AND supported = 0 ORDER BY created_at DESC LIMIT ?",
        params + [limit],
    ).fetchall()

    conn.close()
    return {
        "total_questions": total,
        "unanswered_count": unanswered,
        "no_answer_rate": round(unanswered / total, 4) if total > 0 else 0.0,
        "sample_unanswered": [r[0] for r in samples],
    }


def total_signal_count() -> int:
    """Total number of signals in the database."""
    conn = _get_connection()
    count = conn.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    conn.close()
    return count


def avg_tension(days: Optional[int] = None) -> float:
    """Overall average tension score."""
    conn = _get_connection()
    query = "SELECT AVG(tension_score) FROM signals"
    params: list = []

    if days:
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query += " WHERE created_at >= ?"
        params.append(cutoff)

    result = conn.execute(query, params).fetchone()[0]
    conn.close()
    return round(result, 4) if result else 0.0


def distinct_counties() -> int:
    """Count of distinct counties in the data."""
    conn = _get_connection()
    count = conn.execute(
        "SELECT COUNT(DISTINCT county) FROM signals WHERE county IS NOT NULL"
    ).fetchone()[0]
    conn.close()
    return count
