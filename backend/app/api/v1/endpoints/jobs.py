from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.research_job import ResearchJob
from app.models.project import Project
from app.models.user import User
from app.schemas.research_job import ResearchJobOut
from app.api.v1.deps import get_current_user

router = APIRouter()


@router.get("/{job_uuid}", response_model=ResearchJobOut)
def get_job_status(
    job_uuid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns background job status, progress percentage, and outputs."""
    job = db.query(ResearchJob).filter(ResearchJob.job_uuid == job_uuid).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    project = db.query(Project).filter(Project.id == job.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return job
