"""
models.py - Data models and SQLite persistence for Algorithmic Consensus

Defines data structures (dataclasses) and all database operations.
No ORM -- raw sqlite3 to keep dependencies minimal.

Tables:
  participants  - anonymous users with optional coarse location
  statements    - human-authored text (<140 chars) + embedding + sentiment
  votes         - agree(1) / disagree(-1) / pass(0) per participant per statement
  results       - computed outputs (clusters, consensus) stored as JSON

Privacy: participants identified only by UUID-based anonymous IDs.
No names, emails, phone numbers, or GPS coordinates are ever stored.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import numpy as np

import config


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Participant:
    id: str                  # Anonymous UUID, e.g. "participant_a3f7b2c1"
    created_at: str          # ISO 8601
    location: str = ""       # Optional coarse geographic (city name, never GPS)


@dataclass
class Statement:
    id: int                  # Auto-increment
    author_id: str           # FK -> participants.id
    text: str                # Human-authored, <= 140 chars
    embedding: Optional[bytes] = None   # Serialized numpy array (768-dim float32)
    sentiment: str = ""      # "positive" | "negative" | "neutral"
    sentiment_score: float = 0.0
    created_at: str = ""


@dataclass
class Vote:
    participant_id: str      # FK -> participants.id
    statement_id: int        # FK -> statements.id
    value: int               # 1=agree, -1=disagree, 0=pass
    created_at: str = ""


@dataclass
class ClusterInfo:
    id: int
    label: str               # "Group A", "Group B", etc.
    member_ids: list = field(default_factory=list)
    centroid: Optional[list] = None  # [x, y] in PCA space


@dataclass
class ConsensusResult:
    unity_score: float
    consensus_index: float
    bridge_statements: list  # List of statement IDs
    cluster_count: int
    total_statements: int
    total_participants: int
    generated_at: str = ""


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

def init_db(db_path=None) -> sqlite3.Connection:
    """Create database and tables. Returns connection."""
    path = db_path or config.DB_PATH
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS participants (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            location TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_id TEXT NOT NULL REFERENCES participants(id),
            text TEXT NOT NULL CHECK(length(text) <= 140),
            embedding BLOB,
            sentiment TEXT DEFAULT '',
            sentiment_score REAL DEFAULT 0.0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS votes (
            participant_id TEXT NOT NULL REFERENCES participants(id),
            statement_id INTEGER NOT NULL REFERENCES statements(id),
            value INTEGER NOT NULL CHECK(value IN (-1, 0, 1)),
            created_at TEXT NOT NULL,
            PRIMARY KEY (participant_id, statement_id)
        );

        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_type TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_participant(conn: sqlite3.Connection, location: str = "") -> Participant:
    """Register a new anonymous participant. Returns Participant with generated ID."""
    pid = config.ANON_ID_PREFIX + uuid.uuid4().hex[:8]
    now = _now()
    conn.execute(
        "INSERT INTO participants (id, created_at, location) VALUES (?, ?, ?)",
        (pid, now, location),
    )
    conn.commit()
    return Participant(id=pid, created_at=now, location=location)


def add_statement(
    conn: sqlite3.Connection,
    author_id: str,
    text: str,
    embedding: np.ndarray,
    sentiment: str,
    sentiment_score: float,
) -> Statement:
    """Store a validated statement with its embedding and sentiment."""
    now = _now()
    embedding_bytes = embedding.astype(np.float32).tobytes()
    cursor = conn.execute(
        """INSERT INTO statements (author_id, text, embedding, sentiment, sentiment_score, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (author_id, text, embedding_bytes, sentiment, sentiment_score, now),
    )
    conn.commit()
    return Statement(
        id=cursor.lastrowid,
        author_id=author_id,
        text=text,
        embedding=embedding_bytes,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        created_at=now,
    )


def cast_vote(
    conn: sqlite3.Connection,
    participant_id: str,
    statement_id: int,
    value: int,
) -> Vote:
    """Cast or update a vote. value: 1=agree, -1=disagree, 0=pass."""
    value = int(value)  # Ensure native int (numpy int64 breaks SQLite CHECK)
    if value not in (-1, 0, 1):
        raise ValueError(f"Vote value must be -1, 0, or 1 (got {value})")
    now = _now()
    conn.execute(
        """INSERT INTO votes (participant_id, statement_id, value, created_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(participant_id, statement_id) DO UPDATE SET value=?, created_at=?""",
        (participant_id, int(statement_id), value, now, value, now),
    )
    conn.commit()
    return Vote(
        participant_id=participant_id,
        statement_id=statement_id,
        value=value,
        created_at=now,
    )


def get_vote_matrix(conn: sqlite3.Connection) -> tuple:
    """
    Build the vote matrix from the database.

    Returns:
        matrix: np.ndarray of shape (n_participants, n_statements)
                Values: 1, -1, 0, or NaN (participant did not vote on that statement)
        participant_ids: list of participant ID strings (row order)
        statement_ids: list of statement ID ints (column order)

    Only includes statements with >= MIN_VOTES_PER_STATEMENT votes.
    """
    # Find statements with enough votes
    rows = conn.execute(
        """SELECT statement_id, COUNT(*) as cnt FROM votes
           GROUP BY statement_id HAVING cnt >= ?""",
        (config.MIN_VOTES_PER_STATEMENT,),
    ).fetchall()
    qualified_stmt_ids = sorted([r[0] for r in rows])

    if not qualified_stmt_ids:
        return np.array([]), [], []

    # Get all participants who voted on qualified statements
    placeholders = ",".join("?" * len(qualified_stmt_ids))
    participant_rows = conn.execute(
        f"SELECT DISTINCT participant_id FROM votes WHERE statement_id IN ({placeholders})",
        qualified_stmt_ids,
    ).fetchall()
    pids = sorted([r[0] for r in participant_rows])

    if not pids:
        return np.array([]), [], []

    # Build index maps
    pid_idx = {pid: i for i, pid in enumerate(pids)}
    sid_idx = {sid: j for j, sid in enumerate(qualified_stmt_ids)}

    # Initialize with NaN (unvoted)
    matrix = np.full((len(pids), len(qualified_stmt_ids)), np.nan)

    # Fill in actual votes
    vote_rows = conn.execute(
        f"""SELECT participant_id, statement_id, value FROM votes
            WHERE statement_id IN ({placeholders})""",
        qualified_stmt_ids,
    ).fetchall()

    for pid, sid, val in vote_rows:
        if pid in pid_idx and sid in sid_idx:
            matrix[pid_idx[pid], sid_idx[sid]] = val

    return matrix, pids, qualified_stmt_ids


def get_all_statements(conn: sqlite3.Connection) -> list:
    """Return all statements as Statement objects (without embedding blobs for display)."""
    rows = conn.execute(
        "SELECT id, author_id, text, sentiment, sentiment_score, created_at FROM statements ORDER BY id"
    ).fetchall()
    return [
        Statement(id=r[0], author_id=r[1], text=r[2], sentiment=r[3],
                  sentiment_score=r[4], created_at=r[5])
        for r in rows
    ]


def get_statement_by_id(conn: sqlite3.Connection, stmt_id: int) -> Optional[Statement]:
    """Return a single statement by ID."""
    row = conn.execute(
        "SELECT id, author_id, text, sentiment, sentiment_score, created_at FROM statements WHERE id=?",
        (stmt_id,),
    ).fetchone()
    if not row:
        return None
    return Statement(id=row[0], author_id=row[1], text=row[2], sentiment=row[3],
                     sentiment_score=row[4], created_at=row[5])


def get_participant_locations(conn: sqlite3.Connection) -> dict:
    """Return {participant_id: location} for all participants with a location set."""
    rows = conn.execute(
        "SELECT id, location FROM participants WHERE location != ''"
    ).fetchall()
    return {r[0]: r[1] for r in rows}


def get_stats(conn: sqlite3.Connection) -> dict:
    """Return summary statistics about the current deliberation."""
    p_count = conn.execute("SELECT COUNT(*) FROM participants").fetchone()[0]
    s_count = conn.execute("SELECT COUNT(*) FROM statements").fetchone()[0]
    v_count = conn.execute("SELECT COUNT(*) FROM votes").fetchone()[0]
    coverage = 0.0
    if p_count > 0 and s_count > 0:
        coverage = v_count / (p_count * s_count) * 100
    return {
        "participants": p_count,
        "statements": s_count,
        "votes": v_count,
        "vote_coverage_pct": round(coverage, 1),
    }


def get_next_unvoted_statement(conn: sqlite3.Connection, participant_id: str) -> Optional[Statement]:
    """Return a random statement this participant hasn't voted on yet (excludes own)."""
    row = conn.execute(
        """SELECT id, author_id, text, sentiment, sentiment_score, created_at
           FROM statements
           WHERE id NOT IN (SELECT statement_id FROM votes WHERE participant_id = ?)
             AND author_id != ?
           ORDER BY RANDOM() LIMIT 1""",
        (participant_id, participant_id),
    ).fetchone()
    if not row:
        return None
    return Statement(id=row[0], author_id=row[1], text=row[2],
                     sentiment=row[3], sentiment_score=row[4], created_at=row[5])


def get_participant_votes(conn: sqlite3.Connection, participant_id: str) -> list:
    """Return all votes cast by a participant."""
    rows = conn.execute(
        "SELECT participant_id, statement_id, value, created_at FROM votes WHERE participant_id=? ORDER BY created_at",
        (participant_id,),
    ).fetchall()
    return [Vote(participant_id=r[0], statement_id=r[1], value=r[2], created_at=r[3]) for r in rows]


def get_latest_result(conn: sqlite3.Connection, result_type: str = "consensus") -> Optional[dict]:
    """Return the most recent analysis result as a parsed dict, or None."""
    row = conn.execute(
        "SELECT data_json FROM results WHERE result_type=? ORDER BY id DESC LIMIT 1",
        (result_type,),
    ).fetchone()
    if not row:
        return None
    return json.loads(row[0])


def save_result(conn: sqlite3.Connection, result_type: str, data: dict) -> None:
    """Save a computed result (cluster info, consensus) as JSON."""
    conn.execute(
        "INSERT INTO results (result_type, data_json, created_at) VALUES (?, ?, ?)",
        (result_type, json.dumps(data, ensure_ascii=False, default=str), _now()),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Seed data for testing
# ---------------------------------------------------------------------------

def seed_data(conn: sqlite3.Connection) -> None:
    """
    Populate the database with synthetic data for testing the full pipeline.

    Creates 15 participants across 4 Syrian cities, 10 Arabic statements
    representing diverse opinions, and a realistic vote pattern that should
    produce 2-3 clusters with some bridge statements.
    """
    # Participants: 15 across 4 locations
    locations = (
        ["Damascus"] * 4 + ["Aleppo"] * 4 + ["Idlib"] * 4 + ["Homs"] * 3
    )
    participants = []
    for loc in locations:
        p = create_participant(conn, location=loc)
        participants.append(p)

    # Statements: 10 Arabic statements covering different topics
    # These are realistic deliberation statements about post-conflict priorities
    statements_data = [
        ("نحتاج مدارس أفضل لأطفالنا", "positive", 0.8),                    # We need better schools for our children
        ("الأمان هو أهم شيء الآن", "neutral", 0.5),                         # Safety is the most important thing now
        ("يجب حماية حق الملكية العقارية للجميع", "neutral", 0.6),           # Property rights must be protected for all
        ("نريد محاسبة المسؤولين عن الدمار", "negative", 0.7),              # We want accountability for destruction
        ("الوحدة الوطنية أهم من الانتقام", "positive", 0.9),                # National unity more important than revenge
        ("نحتاج فرص عمل قبل أي شيء آخر", "neutral", 0.5),                 # We need jobs before anything else
        ("يجب أن يكون الدستور الجديد علمانياً", "neutral", 0.4),           # New constitution should be secular
        ("حماية المرأة يجب أن تكون أولوية", "positive", 0.8),              # Protecting women must be a priority
        ("لا نثق بأي حكومة مركزية بعد الآن", "negative", 0.6),            # We don't trust any central government
        ("التعليم والصحة قبل السياسة", "positive", 0.7),                    # Education and health before politics
    ]

    # Create dummy embeddings (768-dim random vectors, normalized)
    # In production these come from sentence-transformers
    rng = np.random.RandomState(42)
    stmt_objects = []
    for text, sentiment, score in statements_data:
        emb = rng.randn(config.EMBEDDING_DIM).astype(np.float32)
        emb = emb / np.linalg.norm(emb)  # normalize
        stmt = add_statement(conn, participants[0].id, text, emb, sentiment, score)
        stmt_objects.append(stmt)

    # Vote patterns: designed to create 2-3 opinion clusters
    # Group 1 (participants 0-4): "pragmatists" - agree on services, neutral on politics
    # Group 2 (participants 5-9): "accountability-focused" - want justice, distrust govt
    # Group 3 (participants 10-14): "unity-focused" - prioritize reconciliation
    vote_patterns = {
        # Statement indices ->        0   1   2   3   4   5   6   7   8   9
        "pragmatist":               [ 1,  1,  1, -1,  0,  1,  0,  1, -1,  1],
        "accountability":           [ 1,  1,  1,  1, -1,  1,  1,  0,  1,  0],
        "unity":                    [ 1,  1,  1, -1,  1,  0, -1,  1, -1,  1],
    }

    def _with_noise(pattern, rng):
        """Add slight randomness so not all group members vote identically."""
        result = list(pattern)
        for i in range(len(result)):
            if rng.random() < 0.15:  # 15% chance to flip
                result[i] = rng.choice([-1, 0, 1])
        return result

    for i, p in enumerate(participants):
        if i < 5:
            votes = _with_noise(vote_patterns["pragmatist"], rng)
        elif i < 10:
            votes = _with_noise(vote_patterns["accountability"], rng)
        else:
            votes = _with_noise(vote_patterns["unity"], rng)

        for j, stmt in enumerate(stmt_objects):
            # Skip some votes randomly (20%) to simulate incomplete participation
            if rng.random() < 0.20:
                continue
            cast_vote(conn, p.id, stmt.id, votes[j])

    print(f"Seeded: {len(participants)} participants, {len(stmt_objects)} statements, votes cast.")
