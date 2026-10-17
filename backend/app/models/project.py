from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("User", back_populates="projects")
    ideas = relationship("Idea", back_populates="project", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="project", cascade="all, delete-orphan")
    comparison_results = relationship("ComparisonResult", back_populates="project", cascade="all, delete-orphan")
    papers = relationship("AcademicPaper", back_populates="project", cascade="all, delete-orphan")
    patents = relationship("PatentRecord", back_populates="project", cascade="all, delete-orphan")
    gap_analyses = relationship("ResearchGapAnalysis", back_populates="project", cascade="all, delete-orphan")
    roadmaps = relationship("ImplementationRoadmap", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project", cascade="all, delete-orphan")
    presentations = relationship("Presentation", back_populates="project", cascade="all, delete-orphan")
    mentor_conversations = relationship("MentorConversation", back_populates="project", cascade="all, delete-orphan")
    research_jobs = relationship("ResearchJob", back_populates="project", cascade="all, delete-orphan")
