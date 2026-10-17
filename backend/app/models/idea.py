from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    problem_statement = Column(Text, nullable=False)
    proposed_solution = Column(Text, nullable=False)
    target_audience = Column(String(255), nullable=False)
    industry = Column(String(100), default="General", nullable=False)
    intended_use_case = Column(Text, default="Core Innovation Workflow", nullable=False)
    expected_benefits = Column(Text, default="Productivity and efficiency gains", nullable=False)
    constraints = Column(Text, nullable=True)
    estimated_budget = Column(String(100), nullable=True)
    technical_preferences = Column(Text, nullable=True)
    is_selected = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="ideas")
    evaluations = relationship("Evaluation", back_populates="idea", cascade="all, delete-orphan")
    gap_analyses = relationship("ResearchGapAnalysis", back_populates="idea", cascade="all, delete-orphan")
    roadmaps = relationship("ImplementationRoadmap", back_populates="idea", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="idea", cascade="all, delete-orphan")
    presentations = relationship("Presentation", back_populates="idea", cascade="all, delete-orphan")
