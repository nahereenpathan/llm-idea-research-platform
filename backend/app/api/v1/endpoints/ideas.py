from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from app.core.database import get_db
from app.models.project import Project
from app.models.idea import Idea
from app.schemas.idea import IdeaCreate, IdeaUpdate, IdeaOut
from app.api.v1.deps import verify_project_ownership, get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/projects/{project_id}/ideas", response_model=List[IdeaOut])
def list_ideas_for_project(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Lists all submitted ideas (up to 3) for the specified project."""
    ideas = db.query(Idea).filter(Idea.project_id == project.id).order_by(Idea.created_at.asc()).all()
    return ideas


@router.post("/projects/{project_id}/ideas", response_model=IdeaOut, status_code=status.HTTP_201_CREATED)
def submit_idea_to_project(
    idea_in: IdeaCreate,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Submits a new idea to the comparison project (enforces maximum of 3 ideas per project)."""
    current_count = db.query(Idea).filter(Idea.project_id == project.id).count()
    if current_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A comparison project can have at most 3 ideas. Please delete an idea before adding another."
        )

    # If first idea, mark as selected by default
    is_first = (current_count == 0)

    idea = Idea(
        project_id=project.id,
        title=idea_in.title,
        problem_statement=idea_in.problem_statement,
        proposed_solution=idea_in.proposed_solution,
        target_audience=idea_in.target_audience,
        industry=idea_in.industry or "General",
        intended_use_case=idea_in.intended_use_case or "Core Innovation Workflow",
        expected_benefits=idea_in.expected_benefits or "Productivity and efficiency gains",
        constraints=idea_in.constraints,
        estimated_budget=idea_in.estimated_budget,
        technical_preferences=idea_in.technical_preferences,
        is_selected=is_first,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(idea)
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(idea)
    return idea


@router.put("/ideas/{idea_id}", response_model=IdeaOut)
def update_idea(
    idea_id: int,
    idea_in: IdeaUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates an idea after verifying the user owns the parent project."""
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")
    
    project = db.query(Project).filter(Project.id == idea.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    for field, val in idea_in.model_dump(exclude_unset=True).items():
        setattr(idea, field, val)

    idea.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(idea)
    return idea


@router.delete("/ideas/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_idea(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes an idea after verifying parent project ownership."""
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")

    project = db.query(Project).filter(Project.id == idea.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(idea)
    db.commit()
    return None


@router.post("/ideas/{idea_id}/select", response_model=IdeaOut)
def set_selected_idea(
    idea_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sets this idea as the active selected candidate for research and implementation."""
    idea = db.query(Idea).filter(Idea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found")

    project = db.query(Project).filter(Project.id == idea.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Unselect all other ideas in project
    db.query(Idea).filter(Idea.project_id == project.id).update({"is_selected": False})
    idea.is_selected = True
    idea.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(idea)
    return idea
