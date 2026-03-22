"""Router: participant management."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_db
from api.schemas import CreateParticipantRequest, ParticipantResponse
import models

router = APIRouter()


@router.post("/participants", response_model=ParticipantResponse)
def create_participant(
    req: CreateParticipantRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    p = models.create_participant(conn, location=req.location)
    return ParticipantResponse(id=p.id, created_at=p.created_at, location=p.location)
