from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Presentation(Base):
    __tablename__ = "presentations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    theme = Column(String(50), default="navy_modern", nullable=False)  # navy_modern, minimalist_clean, academic_slate, startup_cyber
    template_type = Column(String(50), default="hackathon", nullable=False)  # hackathon, college_project, research_proposal, startup_pitch, technical
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="presentations")
    idea = relationship("Idea", back_populates="presentations")
    slides = relationship("Slide", back_populates="presentation", cascade="all, delete-orphan", order_by="Slide.sort_order")


class Slide(Base):
    __tablename__ = "slides"

    id = Column(Integer, primary_key=True, index=True)
    presentation_id = Column(Integer, ForeignKey("presentations.id", ondelete="CASCADE"), nullable=False, index=True)
    slide_number = Column(Integer, nullable=False)
    layout = Column(String(50), default="bullets", nullable=False)  # title, bullets, two_column, architecture, timeline, metrics
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    content_json = Column(JSON, default=dict, nullable=False)  # bullets, left_column, right_column, notes, citations
    sort_order = Column(Integer, default=0, nullable=False)

    presentation = relationship("Presentation", back_populates="slides")
