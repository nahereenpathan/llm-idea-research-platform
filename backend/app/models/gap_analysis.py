from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class ResearchGapAnalysis(Base):
    __tablename__ = "research_gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    
    existing_approaches = Column(JSON, default=list, nullable=False)
    common_findings = Column(JSON, default=list, nullable=False)
    conflicting_findings = Column(JSON, default=list, nullable=False)
    limitations_in_prior_work = Column(JSON, default=list, nullable=False)
    identified_gaps = Column(JSON, default=list, nullable=False)
    suggested_research_questions = Column(JSON, default=list, nullable=False)
    proposed_evaluation_methods = Column(JSON, default=list, nullable=False)
    citations = Column(JSON, default=list, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="gap_analyses")
    idea = relationship("Idea", back_populates="gap_analyses")
