from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.idea import Idea
from app.models.report import Report
from app.models.research_job import ResearchJob
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.api.v1.deps import get_current_user, verify_project_ownership

router = APIRouter()


@router.get("/dashboard/stats", response_model=Dict[str, Any])
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns real dashboard metrics, recent projects, and active research jobs."""
    user_projects = db.query(Project).filter(Project.user_id == current_user.id).all()
    project_ids = [p.id for p in user_projects]

    total_projects = len(user_projects)
    total_ideas = db.query(Idea).filter(Idea.project_id.in_(project_ids)).count() if project_ids else 0
    total_reports = db.query(Report).filter(Report.project_id.in_(project_ids)).count() if project_ids else 0

    # Recent activity / jobs
    recent_jobs = (
        db.query(ResearchJob)
        .filter(ResearchJob.project_id.in_(project_ids))
        .order_by(ResearchJob.created_at.desc())
        .limit(5)
        .all()
    ) if project_ids else []

    recent_projects_out = [
        {
            "id": p.id,
            "title": p.title,
            "domain": p.domain,
            "updated_at": p.updated_at.isoformat(),
            "ideas_count": len(p.ideas)
        }
        for p in sorted(user_projects, key=lambda x: x.updated_at, reverse=True)[:5]
    ]

    return {
        "total_projects": total_projects,
        "ideas_analyzed": total_ideas,
        "reports_generated": total_reports,
        "recent_projects": recent_projects_out,
        "recent_jobs": [
            {
                "id": j.id,
                "job_uuid": j.job_uuid,
                "job_type": j.job_type,
                "status": j.status,
                "progress_percentage": j.progress_percentage,
                "status_message": j.status_message,
                "created_at": j.created_at.isoformat()
            }
            for j in recent_jobs
        ]
    }


@router.get("/", response_model=List[ProjectOut])
def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all projects owned by the authenticated user."""
    projects = (
        db.query(Project)
        .filter(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
        .all()
    )
    result = []
    for p in projects:
        p_dict = ProjectOut.model_validate(p)
        p_dict.idea_count = len(p.ideas)
        result.append(p_dict)
    return result


@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new project owned by current user."""
    project = Project(
        user_id=current_user.id,
        title=project_in.title,
        description=project_in.description,
        domain=project_in.domain,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    p_dict = ProjectOut.model_validate(project)
    p_dict.idea_count = 0
    return p_dict


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project: Project = Depends(verify_project_ownership),
):
    """Gets project details by ID with strict user authorization check."""
    p_dict = ProjectOut.model_validate(project)
    p_dict.idea_count = len(project.ideas)
    return p_dict


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_in: ProjectUpdate,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Updates project title, description, or domain."""
    if project_in.title is not None:
        project.title = project_in.title
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.domain is not None:
        project.domain = project_in.domain
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    p_dict = ProjectOut.model_validate(project)
    p_dict.idea_count = len(project.ideas)
    return p_dict


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Deletes project and cascades to all child ideas, reports, and analyses."""
    db.delete(project)
    db.commit()
    return None
