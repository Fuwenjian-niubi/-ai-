import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..agent import run as agent_run
from ..database import get_db
from ..deps import get_current_user
from ..skills.registry import registry

router = APIRouter(prefix="/api/qa", tags=["qa"])


def _persist(db: Session, user: models.User, req: schemas.QARequest, answer: str, citations: list) -> None:
    if req.session_id is None:
        return
    sess = (
        db.query(models.ChatSession)
        .filter(
            models.ChatSession.id == req.session_id,
            models.ChatSession.user_id == user.id,
        )
        .first()
    )
    if not sess:
        return
    db.add(models.Message(session_id=sess.id, role="user", content=req.question))
    db.add(
        models.Message(
            session_id=sess.id,
            role="assistant",
            content=answer,
            citations=json.dumps(citations, ensure_ascii=False),
        )
    )
    db.commit()


@router.post("", response_model=schemas.QAResponse)
def ask(
    req: schemas.QARequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    kb = db.get(models.KnowledgeBase, req.kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # M3：经 LangGraph 智能体（记忆 + 技能 + RAG）生成回答（带缓存，复问秒回）
    result = agent_run.run_agent_cached(
        kb_id=req.kb_id,
        user_id=user.id,
        query=req.question,
        db=db,
        session_id=req.session_id,
    )

    _persist(db, user, req, result["answer"], result["citations"])

    return schemas.QAResponse(
        answer=result["answer"],
        citations=[schemas.Citation(**c) for c in result["citations"]],
        skill=result["skill"],
        memory_used=result["memory_used"],
    )


@router.post("/stream")
async def ask_stream(
    req: schemas.QARequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """SSE 真·流式问答（Qwen 原生支持 stream=true）。

    后端通过 run_agent_stream 逐 token 推送，首字延迟 1~2s；缓存命中则直接
    返回 done 事件（秒回）。前端 askStream 已支持增量渲染。

    事件格式（text/event-stream）：
      data: {"type":"token","content":"你"}
      data: {"type":"done","answer":...,"citations":[...],"skill":...,"memory_used":[...]}
      data: {"type":"error","message":"..."}
      data: [DONE]
    """
    kb = db.get(models.KnowledgeBase, req.kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    async def event_source():
        saved_answer = ""
        saved_citations: list = []
        saved_skill = ""
        saved_memory: list = []
        try:
            async for ev in agent_run.run_agent_stream(
                kb_id=req.kb_id,
                user_id=user.id,
                query=req.question,
                db=db,
                session_id=req.session_id,
            ):
                if ev["type"] == "token":
                    yield f"data: {json.dumps({'type': 'token', 'content': ev['content']}, ensure_ascii=False)}\n\n"
                elif ev["type"] == "done":
                    saved_answer = ev["answer"]
                    saved_citations = ev["citations"]
                    saved_skill = ev["skill"]
                    saved_memory = ev["memory_used"]
                    yield f"data: {json.dumps({'type': 'done', 'answer': saved_answer, 'citations': saved_citations, 'skill': saved_skill, 'memory_used': saved_memory}, ensure_ascii=False)}\n\n"
                elif ev["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': ev['message']}, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    return
        except Exception as e:  # noqa: BLE001
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            return

        # 持久化（流结束后）
        try:
            _persist(db, user, req, saved_answer, saved_citations)
        except Exception:  # noqa: BLE001
            pass

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/skills")
def list_skills(_user: models.User = Depends(get_current_user)):
    """列出已注册的可插拔技能（Agent 可用能力）。"""
    return {
        "skills": [
            {"name": s.name, "description": s.description}
            for s in registry.list()
        ]
    }
