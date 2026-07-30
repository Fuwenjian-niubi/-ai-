import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=schemas.SessionOut, status_code=201)
def create_session(
    req: schemas.SessionCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    s = models.ChatSession(user_id=user.id, title=req.title or "新对话")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.get("", response_model=list[schemas.SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == user.id)
        .order_by(models.ChatSession.updated_at.desc())
        .all()
    )


@router.get("/{sid}", response_model=schemas.SessionOut)
def get_session(
    sid: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    s = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.id == sid,
            models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="会话不存在")
    return s


@router.patch("/{sid}", response_model=schemas.SessionOut)
def rename_session(
    sid: int,
    req: schemas.SessionUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    s = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.id == sid,
            models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="会话不存在")
    s.title = req.title
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{sid}", status_code=204)
def delete_session(
    sid: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    s = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.id == sid,
            models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete(s)
    db.commit()


@router.get("/{sid}/messages")
def get_messages(
    sid: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """返回该会话下持久化的消息（含助手回答的引用），用于历史回溯。"""
    s = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.id == sid,
            models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not s:
        raise HTTPException(status_code=404, detail="会话不存在")
    msgs = (
        db.query(models.Message)
        .filter(models.Message.session_id == sid)
        .order_by(models.Message.id.asc())
        .all()
    )
    return [
        {
            "role": m.role,
            "content": m.content,
            "citations": json.loads(m.citations or "[]"),
        }
        for m in msgs
    ]
