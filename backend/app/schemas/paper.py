from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ResearchSourceInfo(BaseModel):
    id: str
    name: str
    requires_key: bool
    is_configured: bool
    status: str  # "active" or "unconfigured"
    description: str


class AcademicPaperBase(BaseModel):
    external_id: Optional[str] = None
    source: str = "openalex"
    title: str
    authors: List[str] = []
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    abstract: Optional[str] = None
    has_abstract: Optional[bool] = None
    doi: Optional[str] = None
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None
    landing_page_url: Optional[str] = None
    repository_url: Optional[str] = None
    venue: Optional[str] = None
    citation_count: int = 0
    is_open_access: Optional[bool] = False
    open_access_status: Optional[str] = None
    is_saved_to_library: bool = False
    user_notes: Optional[str] = None
    ai_summary: Optional[str] = None


class AcademicPaperCreate(AcademicPaperBase):
    pass


class AcademicPaperUpdate(BaseModel):
    is_saved_to_library: Optional[bool] = None
    user_notes: Optional[str] = None
    ai_summary: Optional[str] = None


class AcademicPaperOut(AcademicPaperBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaperSearchResponse(BaseModel):
    query: str
    source: str
    search_type: str = "keyword"
    page: int = 1
    limit: int = 10
    total_count: Optional[int] = None
    results: List[Dict[str, Any]]


class PaperSearchRequest(BaseModel):
    query: str
    source: Optional[str] = "openalex"
    search_type: Optional[str] = "keyword"
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    page: Optional[int] = 1
    limit: Optional[int] = 10

