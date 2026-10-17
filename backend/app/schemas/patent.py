from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PatentSourceInfo(BaseModel):
    id: str
    name: str
    requires_key: bool
    is_configured: bool
    status: str  # "active" or "unconfigured"
    description: str


class PatentRecordBase(BaseModel):
    patent_number: str
    title: str
    inventors: List[str] = []
    publication_date: Optional[str] = None
    filing_date: Optional[str] = None
    abstract: Optional[str] = None
    status: Optional[str] = None
    source: str = "uspto"
    source_url: Optional[str] = None
    is_saved: bool = False
    similarity_notes: Optional[str] = None


class PatentRecordCreate(PatentRecordBase):
    pass


class PatentRecordUpdate(BaseModel):
    is_saved: Optional[bool] = None
    similarity_notes: Optional[str] = None


class PatentRecordOut(PatentRecordBase):
    id: int
    project_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatentSearchResponse(BaseModel):
    query: str
    source: str
    search_type: str = "keyword"
    page: int = 1
    limit: int = 10
    total_count: Optional[int] = None
    disclaimer: str
    results: List[Dict[str, Any]]


class PatentSearchRequest(BaseModel):
    query: str
    source: Optional[str] = "uspto"
    search_type: Optional[str] = "keyword"
    page: Optional[int] = 1
    limit: Optional[int] = 10

