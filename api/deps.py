"""
deps.py - FastAPI dependency injection

Provides:
    - get_db(): yields a fresh SQLite connection per request (closed after)
    - get_processor(): returns the shared InputProcessor singleton
    - lifespan(): app startup/shutdown (pre-loads InputProcessor, seeds data)
"""

import os
import sqlite3
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Ensure project root is on sys.path so `import config`, `import models` etc. work
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import config
import models

_processor = None
_tables_created = False


def _check_ml_available() -> bool:
    """Check if heavy ML packages are actually importable."""
    try:
        import sentence_transformers  # noqa: F401
        import camel_tools  # noqa: F401
        return True
    except ImportError:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup: ensure tables exist, pre-load InputProcessor, seed data."""
    global _processor, _tables_created
    # Create tables once at startup
    startup_conn = models.init_db()
    _tables_created = True

    # Seed demo data if database is empty
    stats = models.get_stats(startup_conn)
    if stats["participants"] == 0:
        print("[startup] Empty database detected, seeding demo data...")
        models.seed_data(startup_conn)
        print("[startup] Demo data seeded successfully")

    startup_conn.close()

    # Only try loading InputProcessor if ML packages are installed
    if _check_ml_available():
        try:
            from voice import InputProcessor
            _processor = InputProcessor()
            # Force-load one model to verify it actually works (not just lazy init)
            _processor._load_embedding_model()
            print("[startup] InputProcessor loaded (ML features enabled)")
        except Exception as e:
            _processor = None
            print(f"[startup] InputProcessor unavailable: {e}")
            print("[startup] Text-only mode (no audio, no embeddings, no sentiment)")
    else:
        _processor = None
        print("[startup] ML packages not installed - running in lite mode")
        print("[startup] Text-only mode (no audio, no embeddings, no sentiment)")

    yield


def get_db():
    """Yield a thread-safe SQLite connection per request.

    Uses check_same_thread=False because FastAPI runs sync endpoints
    in a threadpool -- the connection may be created on one thread and
    used/closed on another.  Each request gets its own connection,
    so there is no concurrent access to a single connection object.
    """
    global _tables_created
    conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    if not _tables_created:
        # Fallback: ensure tables exist if lifespan hasn't run
        models.init_db()
        _tables_created = True
    try:
        yield conn
    finally:
        conn.close()


def get_processor():
    """Return the shared InputProcessor singleton (None in lite mode)."""
    return _processor
