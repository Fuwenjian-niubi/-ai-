import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..agent.cache import invalidate_kb
from ..database import get_db
from ..deps import get_current_user, require_admin
from ..rag import ingest

router = APIRouter(prefix="/api/kb", tags=["knowledge-base(admin)"])

UPLOAD_DIR = os.path.join("data", "uploads")


@router.post("", response_model=schemas.KBOut, status_code=201)
def create_kb(
    req: schemas.KBCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    kb = models.KnowledgeBase(
        name=req.name, description=req.description, spot=req.spot
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


@router.get("", response_model=list[schemas.KBOut])
def list_kbs(
    db: Session = Depends(get_db), _: models.User = Depends(get_current_user)
):
    return (
        db.query(models.KnowledgeBase)
        .order_by(models.KnowledgeBase.created_at.desc())
        .all()
    )


@router.get("/{kb_id}/documents", response_model=list[schemas.DocOut])
def list_documents(
    kb_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    return (
        db.query(models.Document)
        .filter(models.Document.kb_id == kb_id)
        .order_by(models.Document.created_at.desc())
        .all()
    )


@router.post("/{kb_id}/documents", response_model=schemas.FileUploadResponse)
def upload_document(
    kb_id: int,
    file: UploadFile,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    kb = db.get(models.KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1]
    safe_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        chunk_count = ingest.ingest_document(kb_id, save_path, file.filename or safe_name)
    except Exception as e:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=400, detail=f"摄入失败: {e}")

    if chunk_count == 0:
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=400, detail="文档无可提取文本")

    doc = models.Document(
        kb_id=kb_id, filename=file.filename or safe_name, chunk_count=chunk_count
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    # 知识库内容已变更，令相关答案缓存失效（避免返回旧知识的回答）
    invalidate_kb(kb_id)
    return schemas.FileUploadResponse(
        document_id=doc.id, filename=doc.filename, chunk_count=chunk_count
    )


@router.delete("/{kb_id}", status_code=204)
def delete_kb(
    kb_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    kb = db.get(models.KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    try:
        from ..rag.chroma_store import collection_name, get_client

        get_client().delete_collection(name=collection_name(kb_id))
    except Exception:
        pass  # 向量库集合可能尚不存在
    db.delete(kb)
    db.commit()
    invalidate_kb(kb_id)  # 知识库已删，清掉该库所有缓存
