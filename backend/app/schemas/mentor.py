from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel


class MentorMessageOut(BaseModel):
    id: int
    conversation_id: int
    sender: str
    content: str
    cited_sources: List[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class MentorConversationCreate(BaseModel):
    project_id: Optional[int] = None
    idea_id: Optional[int] = None
    mode: str = "idea"  # idea, research, technical, product, business, validation, pitch
    title: Optional[str] = "New Mentoring Session"


class MentorConversationOut(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int]
    idea_id: Optional[int]
    mode: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MentorMessageOut] = []

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    content: str
