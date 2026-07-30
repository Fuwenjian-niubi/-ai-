from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), default="user", nullable=False)  # admin | user
    created_at = Column(DateTime, default=utcnow, nullable=False)

    sessions = relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan"
    )


class ChatSession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="sessions")


class KnowledgeBase(Base):
    """多景点知识库：一级实体，检索时按 kb 隔离。"""

    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    spot = Column(String(200), default="")  # 关联景点名
    created_at = Column(DateTime, default=utcnow, nullable=False)

    documents = relationship(
        "Document", back_populates="kb", cascade="all, delete-orphan"
    )


class Document(Base):
    """已摄入的源文件记录（文本块实际存储在 Chroma）。"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    kb = relationship("KnowledgeBase", back_populates="documents")


class Message(Base):
    """预留：M3 持久化对话记录时使用。"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    citations = Column(Text, default="")  # JSON 字符串，引用片段
    created_at = Column(DateTime, default=utcnow, nullable=False)
