from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class SessionCreate(BaseModel):
    title: str | None = None


class SessionUpdate(BaseModel):
    title: str


class SessionOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime


# ===== 知识库 / 文档（M2，admin 管理）=====
class KBCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    spot: str = ""


class KBOut(BaseModel):
    id: int
    name: str
    description: str
    spot: str
    created_at: datetime


class DocOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    chunk_count: int
    created_at: datetime


class FileUploadResponse(BaseModel):
    document_id: int
    filename: str
    chunk_count: int


# ===== 问答（M2，带引用溯源）=====
class QARequest(BaseModel):
    kb_id: int
    question: str = Field(..., min_length=1)
    session_id: int | None = None


class Citation(BaseModel):
    index: int
    source: str | None = None
    content: str


class QAResponse(BaseModel):
    answer: str
    citations: list[Citation]
    skill: str = ""              # 本次命中的技能
    memory_used: list[str] = []  # 召回的长期记忆片段
