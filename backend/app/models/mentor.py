from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class MentorConversation(Base):
    __tablename__ = "mentor_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True)
    mode = Column(String(50), default="idea", nullable=False)  # idea, research, technical, product, business, validation, pitch
    title = Column(String(255), default="New Mentoring Session", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="mentor_conversations")
    project = relationship("Project", back_populates="mentor_conversations")
    idea = relationship("Idea")
    messages = relationship("MentorMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="MentorMessage.created_at")


class MentorMessage(Base):
    __tablename__ = "mentor_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("mentor_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # "user" or "mentor"
    content = Column(Text, nullable=False)
    cited_sources = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    conversation = relationship("MentorConversation", back_populates="messages")
