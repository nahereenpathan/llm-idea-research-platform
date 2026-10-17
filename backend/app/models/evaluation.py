from sqlalchemy import Column, Integer, Float, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Dimension scores (1 to 10 for each dimension):
    # - problem_significance
    # - target_user_clarity
    # - technical_feasibility
    # - implementation_complexity
    # - estimated_development_cost
    # - adoption_potential
    # - competitive_landscape
    # - novelty
    # - security_privacy_ethics
    # - evidence_quality
    dimension_scores = Column(JSON, nullable=False)
    overall_score = Column(Float, nullable=False)
    
    strengths = Column(JSON, nullable=False, default=list)
    weaknesses = Column(JSON, nullable=False, default=list)
    risks = Column(JSON, nullable=False, default=list)
    evidence_notes = Column(JSON, nullable=False, default=list)
    missing_information = Column(JSON, nullable=False, default=list)
    recommended_experiments = Column(JSON, nullable=False, default=list)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="evaluations")
    idea = relationship("Idea", back_populates="evaluations")


class ComparisonResult(Base):
    __tablename__ = "comparison_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    configured_weights = Column(JSON, nullable=False)
    recommended_idea_id = Column(Integer, ForeignKey("ideas.id", ondelete="SET NULL"), nullable=True)
    recommendation_rationale = Column(Text, nullable=False)
    tradeoff_analysis = Column(JSON, nullable=False, default=dict)
    is_tie = Column(Integer, default=0, nullable=False)  # 0: clear winner, 1: tie/uncertainty
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="comparison_results")
    recommended_idea = relationship("Idea")
