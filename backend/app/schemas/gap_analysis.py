from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CitationRef(BaseModel):
    source_type: str  # paper or patent
    title: str
    external_id: str
    source_url: str
    relevance_note: str


class ResearchGapAnalysisOut(BaseModel):
    id: int
    project_id: int
    idea_id: int
    existing_approaches: List[str]
    common_findings: List[str]
    conflicting_findings: List[str]
    limitations_in_prior_work: List[str]
    identified_gaps: List[str]
    suggested_research_questions: List[str]
    proposed_evaluation_methods: List[str]
    citations: List[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class GapAnalysisGenerateRequest(BaseModel):
    idea_id: int
