from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    domain: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None


class ProjectOut(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    idea_count: Optional[int] = 0

    class Config:
        from_attributes = True
