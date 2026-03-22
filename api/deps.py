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
from voice import InputProcessor

_processor = None
_tables_created = False


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

    # Load InputProcessor with all ML models
    _processor = InputProcessor()
    print("[startup] InputProcessor created, models will lazy-load on first use")

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
    """Return the shared InputProcessor singleton."""
    return _processor
