from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel


class ResearchJobOut(BaseModel):
    id: int
    job_uuid: str
    project_id: int
    job_type: str
    status: str
    progress_percentage: int
    status_message: Optional[str]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
