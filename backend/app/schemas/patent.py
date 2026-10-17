from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel


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

    class Config:
        from_attributes = True


class PatentSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
