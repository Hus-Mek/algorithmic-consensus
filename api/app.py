"""
app.py - FastAPI application factory

Wires together CORS, routers, lifespan, and (optionally) static file serving.

Launch:
    uvicorn api.app:app --reload --port 8000
"""

import os
import sys

# Ensure project root is on sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.deps import lifespan
from api.routers import participants, statements, votes, status, analysis

app = FastAPI(
    title="Algorithmic Consensus API",
    description="AI-driven deliberative framework for post-conflict peacebuilding",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(participants.router, prefix="/api", tags=["participants"])
app.include_router(statements.router, prefix="/api", tags=["statements"])
app.include_router(votes.router, prefix="/api", tags=["votes"])
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

# Serve React production build if it exists
_frontend_dist = os.path.join(_project_root, "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
