"""Router: deliberation status."""

import sqlite3

from fastapi import APIRouter, Depends

from api.deps import get_db
from api.schemas import StatusResponse
import models

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
def get_status(conn: sqlite3.Connection = Depends(get_db)):
    stats = models.get_stats(conn)
    return StatusResponse(**stats)
