"""Router: voting operations."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_db
from api.schemas import CastVoteRequest, VoteResponse, StatementResponse
import models

router = APIRouter()


@router.post("/votes", response_model=VoteResponse)
def cast_vote(
    req: CastVoteRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    try:
        v = models.cast_vote(conn, req.participant_id, req.statement_id, req.value)
    except (ValueError, Exception) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return VoteResponse(
        participant_id=v.participant_id,
        statement_id=v.statement_id,
        value=v.value,
        created_at=v.created_at,
    )


@router.get("/votes/next/{participant_id}")
def get_next_statement(
    participant_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    stmt = models.get_next_unvoted_statement(conn, participant_id)
    if not stmt:
        return None
    return StatementResponse(
        id=stmt.id,
        text=stmt.text,
        sentiment=stmt.sentiment,
        sentiment_score=stmt.sentiment_score,
        created_at=stmt.created_at,
    )


@router.get("/votes/history/{participant_id}", response_model=list[VoteResponse])
def get_vote_history(
    participant_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    votes = models.get_participant_votes(conn, participant_id)
    return [
        VoteResponse(
            participant_id=v.participant_id,
            statement_id=v.statement_id,
            value=v.value,
            created_at=v.created_at,
        )
        for v in votes
    ]
