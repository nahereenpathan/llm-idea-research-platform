from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class IdeaBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    problem_statement: str = Field(..., min_length=10)
    proposed_solution: str = Field(..., min_length=10)
    target_audience: str = Field(..., min_length=2)
    industry: str = Field(..., min_length=2)
    intended_use_case: str = Field(..., min_length=5)
    expected_benefits: str = Field(..., min_length=5)
    constraints: Optional[str] = None
    estimated_budget: Optional[str] = None
    technical_preferences: Optional[str] = None


class IdeaCreate(IdeaBase):
    pass


class IdeaUpdate(BaseModel):
    title: Optional[str] = None
    problem_statement: Optional[str] = None
    proposed_solution: Optional[str] = None
    target_audience: Optional[str] = None
    industry: Optional[str] = None
    intended_use_case: Optional[str] = None
    expected_benefits: Optional[str] = None
    constraints: Optional[str] = None
    estimated_budget: Optional[str] = None
    technical_preferences: Optional[str] = None
    is_selected: Optional[bool] = None


class IdeaOut(IdeaBase):
    id: int
    project_id: int
    is_selected: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
