"""Router: statement submission and listing."""

import os
import sqlite3
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from api.deps import get_db, get_processor
from api.schemas import StatementResponse, SubmitStatementRequest
import models

router = APIRouter()


def _stmt_to_response(stmt: models.Statement) -> StatementResponse:
    return StatementResponse(
        id=stmt.id,
        text=stmt.text,
        sentiment=stmt.sentiment,
        sentiment_score=stmt.sentiment_score,
        created_at=stmt.created_at,
    )


@router.get("/statements", response_model=list[StatementResponse])
def list_statements(conn: sqlite3.Connection = Depends(get_db)):
    stmts = models.get_all_statements(conn)
    return [_stmt_to_response(s) for s in stmts]


@router.get("/statements/{stmt_id}", response_model=StatementResponse)
def get_statement(stmt_id: int, conn: sqlite3.Connection = Depends(get_db)):
    stmt = models.get_statement_by_id(conn, stmt_id)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    return _stmt_to_response(stmt)


@router.post("/statements", response_model=StatementResponse)
def submit_text_statement(
    req: SubmitStatementRequest,
    conn: sqlite3.Connection = Depends(get_db),
    processor=Depends(get_processor),
):
    # Check participant exists (may be stale after DB reset)
    row = conn.execute("SELECT 1 FROM participants WHERE id=?", (req.author_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="participant_not_found")
    try:
        result = processor.process_input(text=req.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    stmt = models.add_statement(
        conn,
        author_id=req.author_id,
        text=result["text"],
        embedding=result["embedding"],
        sentiment=result["sentiment"],
        sentiment_score=result["sentiment_score"],
    )
    return _stmt_to_response(stmt)


@router.post("/statements/audio", response_model=StatementResponse)
async def submit_audio_statement(
    author_id: str = Form(...),
    audio: UploadFile = File(...),
    conn: sqlite3.Connection = Depends(get_db),
    processor=Depends(get_processor),
):
    # Check participant exists (may be stale after DB reset)
    row = conn.execute("SELECT 1 FROM participants WHERE id=?", (author_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="participant_not_found")
    suffix = os.path.splitext(audio.filename or "recording.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = processor.process_input(audio_path=tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        os.unlink(tmp_path)

    stmt = models.add_statement(
        conn,
        author_id=author_id,
        text=result["text"],
        embedding=result["embedding"],
        sentiment=result["sentiment"],
        sentiment_score=result["sentiment_score"],
    )
    return _stmt_to_response(stmt)
