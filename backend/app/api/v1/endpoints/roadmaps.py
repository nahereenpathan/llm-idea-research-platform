from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from app.core.database import get_db
from app.models.project import Project
from app.models.idea import Idea
from app.models.roadmap import ImplementationRoadmap
from app.schemas.roadmap import (
    ImplementationRoadmapOut, RoadmapGenerateRequest, TaskStatusUpdateRequest
)
from app.api.v1.deps import verify_project_ownership
from app.services.ai.factory import get_llm_provider

router = APIRouter()


@router.post("/projects/{project_id}/roadmap/generate", response_model=ImplementationRoadmapOut, status_code=status.HTTP_201_CREATED)
def generate_roadmap(
    req: RoadmapGenerateRequest,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Generates a practical, phased implementation roadmap, custom technology stack recommendation,
    database schema entities, API specifications, and interactive task breakdown.
    """
    idea = db.query(Idea).filter(Idea.id == req.idea_id, Idea.project_id == project.id).first()
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found in this project")

    llm = get_llm_provider()
    prompt = (
        f"Idea Title: {idea.title}\n"
        f"Problem Statement: {idea.problem_statement}\n"
        f"Proposed Solution: {idea.proposed_solution}\n"
        f"Target Audience: {idea.target_audience}\n"
        f"Industry: {idea.industry}\n"
        f"Intended Use Case: {idea.intended_use_case}\n"
        f"Technical Preferences: {idea.technical_preferences or 'Standard production stack'}\n"
        f"Constraints: {idea.constraints or 'Standard startup budget'}\n\n"
        "Generate a complete, structured implementation roadmap with:\n"
        "- objectives\n"
        "- functional_requirements\n"
        "- nonfunctional_requirements\n"
        "- mvp_scope\n"
        "- phased_milestones (phase, duration, deliverables)\n"
        "- suggested_database_entities (name, purpose)\n"
        "- api_design_endpoints (method, path, description)\n"
        "- recommended_tech_stack (frontend, backend, database, background_tasks, testing - with specific rationale)\n"
        "- task_breakdown (id, phase, title, estimated_days, status)\n"
        "- security_considerations\n"
        "- risks_and_mitigations (risk, mitigation)\n"
        "- estimated_effort_ranges (optimistic_weeks, realistic_weeks, conservative_weeks)\n"
        "Tailor stack recommendations to this specific idea's technical demands."
    )

    sys_prompt = "You are a Principal Software Architect and DevOps Lead. Formulate robust, phased engineering plans."
    roadmap_data = llm.generate_structured(prompt, sys_prompt)

    # Delete previous roadmap for this idea
    db.query(ImplementationRoadmap).filter(
        ImplementationRoadmap.project_id == project.id,
        ImplementationRoadmap.idea_id == idea.id
    ).delete()

    roadmap = ImplementationRoadmap(
        project_id=project.id,
        idea_id=idea.id,
        objectives=roadmap_data.get("objectives", ["Launch MVP", "Verify product-market fit"]),
        functional_requirements=roadmap_data.get("functional_requirements", ["User authentication", "Core workflow execution"]),
        nonfunctional_requirements=roadmap_data.get("nonfunctional_requirements", ["Sub-second latency", "Role-based security"]),
        mvp_scope=roadmap_data.get("mvp_scope", ["Core functionality and basic dashboard"]),
        phased_milestones=roadmap_data.get("phased_milestones", []),
        suggested_database_entities=roadmap_data.get("suggested_database_entities", []),
        api_design_endpoints=roadmap_data.get("api_design_endpoints", []),
        recommended_tech_stack=roadmap_data.get("recommended_tech_stack", {}),
        task_breakdown=roadmap_data.get("task_breakdown", []),
        security_considerations=roadmap_data.get("security_considerations", []),
        risks_and_mitigations=roadmap_data.get("risks_and_mitigations", []),
        estimated_effort_ranges=roadmap_data.get("estimated_effort_ranges", {"realistic_weeks": 8}),
        created_at=datetime.now(timezone.utc)
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    return roadmap


@router.get("/projects/{project_id}/roadmap", response_model=List[ImplementationRoadmapOut])
def get_project_roadmaps(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Retrieves all generated implementation roadmaps for the project."""
    roadmaps = db.query(ImplementationRoadmap).filter(ImplementationRoadmap.project_id == project.id).all()
    return roadmaps


@router.put("/projects/{project_id}/roadmap/tasks/{task_id}", response_model=ImplementationRoadmapOut)
def update_task_status(
    task_id: str,
    status_in: TaskStatusUpdateRequest,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Updates the completion status ('todo', 'in_progress', 'done') of a roadmap task."""
    roadmap = db.query(ImplementationRoadmap).filter(ImplementationRoadmap.project_id == project.id).order_by(ImplementationRoadmap.created_at.desc()).first()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No roadmap found for project")

    tasks = list(roadmap.task_breakdown)
    updated = False
    for t in tasks:
        if str(t.get("id")) == str(task_id):
            t["status"] = status_in.status
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found in roadmap")

    roadmap.task_breakdown = tasks
    # Force SQLAlchemy change detection for JSON field
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(roadmap, "task_breakdown")
    db.commit()
    db.refresh(roadmap)
    return roadmap
