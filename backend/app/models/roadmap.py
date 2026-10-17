from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class ImplementationRoadmap(Base):
    __tablename__ = "implementation_roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True)

    objectives = Column(JSON, default=list, nullable=False)
    functional_requirements = Column(JSON, default=list, nullable=False)
    nonfunctional_requirements = Column(JSON, default=list, nullable=False)
    mvp_scope = Column(JSON, default=list, nullable=False)
    phased_milestones = Column(JSON, default=list, nullable=False)
    suggested_database_entities = Column(JSON, default=list, nullable=False)
    api_design_endpoints = Column(JSON, default=list, nullable=False)
    recommended_tech_stack = Column(JSON, default=dict, nullable=False)
    task_breakdown = Column(JSON, default=list, nullable=False)
    security_considerations = Column(JSON, default=list, nullable=False)
    risks_and_mitigations = Column(JSON, default=list, nullable=False)
    estimated_effort_ranges = Column(JSON, default=dict, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="roadmaps")
    idea = relationship("Idea", back_populates="roadmaps")
