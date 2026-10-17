from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class SlideBase(BaseModel):
    slide_number: int
    layout: str = "bullets"  # title, bullets, two_column, architecture, timeline, metrics
    title: str
    subtitle: Optional[str] = None
    content_json: Dict[str, Any] = {}
    sort_order: int = 0


class SlideCreate(SlideBase):
    pass


class SlideUpdate(BaseModel):
    slide_number: Optional[int] = None
    layout: Optional[str] = None
    title: Optional[str] = None
    subtitle: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    sort_order: Optional[int] = None


class SlideOut(SlideBase):
    id: int
    presentation_id: int

    class Config:
        from_attributes = True


class PresentationBase(BaseModel):
    title: str
    theme: str = "navy_modern"
    template_type: str = "hackathon"


class PresentationCreate(BaseModel):
    idea_id: Optional[int] = None
    title: Optional[str] = None
    theme: Optional[str] = "navy_modern"
    template_type: Optional[str] = "hackathon"


class PresentationUpdate(BaseModel):
    title: Optional[str] = None
    theme: Optional[str] = None
    template_type: Optional[str] = None


class PresentationOut(PresentationBase):
    id: int
    project_id: int
    idea_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    slides: List[SlideOut] = []

    class Config:
        from_attributes = True
