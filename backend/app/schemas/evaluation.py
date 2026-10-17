from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DimensionScores(BaseModel):
    problem_significance: float = Field(..., ge=1.0, le=10.0)
    target_user_clarity: float = Field(..., ge=1.0, le=10.0)
    technical_feasibility: float = Field(..., ge=1.0, le=10.0)
    implementation_complexity: float = Field(..., ge=1.0, le=10.0)
    estimated_development_cost: float = Field(..., ge=1.0, le=10.0)
    adoption_potential: float = Field(..., ge=1.0, le=10.0)
    competitive_landscape: float = Field(..., ge=1.0, le=10.0)
    novelty: float = Field(..., ge=1.0, le=10.0)
    security_privacy_ethics: float = Field(..., ge=1.0, le=10.0)
    evidence_quality: float = Field(..., ge=1.0, le=10.0)


class DimensionWeights(BaseModel):
    problem_significance: float = 1.0
    target_user_clarity: float = 1.0
    technical_feasibility: float = 1.0
    implementation_complexity: float = 1.0
    estimated_development_cost: float = 1.0
    adoption_potential: float = 1.0
    competitive_landscape: float = 1.0
    novelty: float = 1.0
    security_privacy_ethics: float = 1.0
    evidence_quality: float = 1.0


class EvaluationOut(BaseModel):
    id: int
    project_id: int
    idea_id: int
    dimension_scores: Dict[str, float]
    overall_score: float
    strengths: List[str]
    weaknesses: List[str]
    risks: List[str]
    evidence_notes: List[str]
    missing_information: List[str]
    recommended_experiments: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ComparisonRequest(BaseModel):
    weights: Optional[DimensionWeights] = None


class ComparisonResultOut(BaseModel):
    id: int
    project_id: int
    configured_weights: Dict[str, float]
    recommended_idea_id: Optional[int]
    recommendation_rationale: str
    tradeoff_analysis: Dict[str, Any]
    is_tie: int
    created_at: datetime

    class Config:
        from_attributes = True


class FullProjectEvaluationResponse(BaseModel):
    evaluations: List[EvaluationOut]
    comparison: Optional[ComparisonResultOut]
    ideas: List[Any]
