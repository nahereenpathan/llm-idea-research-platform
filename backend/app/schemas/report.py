from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class ReportBase(BaseModel):
    report_type: str  # evaluation, proposal, abstract, feasibility, gap_report, full_documentation
    title: str
    content_markdown: str
    content_json: Optional[Dict[str, Any]] = {}


class ReportCreate(BaseModel):
    idea_id: Optional[int] = None
    report_type: str
    title: Optional[str] = None


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    content_markdown: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None


class ReportOut(ReportBase):
    id: int
    project_id: int
    idea_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
