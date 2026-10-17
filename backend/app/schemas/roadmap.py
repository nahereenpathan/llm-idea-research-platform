from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TaskItem(BaseModel):
    id: str
    phase: str
    title: str
    description: Optional[str] = ""
    estimated_days: int = 2
    status: str = "todo"  # todo, in_progress, done
    priority: str = "medium"  # high, medium, low
    dependencies: List[str] = []


class TaskStatusUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    title: Optional[str] = None
    estimated_days: Optional[int] = None
    dependencies: Optional[List[str]] = None


class ImplementationRoadmapOut(BaseModel):
    id: int
    project_id: int
    idea_id: int
    objectives: List[str]
    functional_requirements: List[str]
    nonfunctional_requirements: List[str]
    mvp_scope: List[str]
    phased_milestones: List[Dict[str, Any]]
    suggested_database_entities: List[Dict[str, Any]]
    api_design_endpoints: List[Dict[str, Any]]
    recommended_tech_stack: Dict[str, Any]
    task_breakdown: List[Dict[str, Any]]
    security_considerations: List[str]
    risks_and_mitigations: List[Dict[str, Any]]
    estimated_effort_ranges: Dict[str, Any]
    effort_estimate_assumptions: Optional[List[str]] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoadmapGenerateRequest(BaseModel):
    idea_id: int


class RoadmapUpdateRequest(BaseModel):
    task_breakdown: Optional[List[Dict[str, Any]]] = None
    objectives: Optional[List[str]] = None
    mvp_scope: Optional[List[str]] = None
