from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AcademicPaperBase(BaseModel):
    external_id: Optional[str] = None
    source: str = "openalex"
    title: str
    authors: List[str] = []
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    abstract: Optional[str] = None
    doi: Optional[str] = None
    source_url: Optional[str] = None
    citation_count: int = 0
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



class PaperSearchRequest(BaseModel):
    query: str
    source: Optional[str] = "openalex"
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    limit: Optional[int] = 10
