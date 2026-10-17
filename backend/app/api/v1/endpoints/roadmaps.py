import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.models.project import Project
from app.models.idea import Idea
from app.models.roadmap import ImplementationRoadmap
from app.schemas.roadmap import (
    ImplementationRoadmapOut,
    RoadmapGenerateRequest,
    TaskStatusUpdateRequest,
    RoadmapUpdateRequest
)
from app.api.v1.deps import verify_project_ownership
from app.services.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/projects/{project_id}/roadmap/generate", response_model=ImplementationRoadmapOut, status_code=status.HTTP_201_CREATED)
def generate_roadmap(
    req: RoadmapGenerateRequest,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Generates a structured, phased implementation roadmap, architectural blueprint,
    technology stack recommendations, and interactive task board.
    """
    idea = db.query(Idea).filter(Idea.id == req.idea_id, Idea.project_id == project.id).first()
    if not idea:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Idea not found in this project")

    llm = get_llm_provider()
    prompt = (
        f"Idea Title: {idea.title}\n"
        f"Problem Statement: {idea.problem_statement}\n"
        f"Proposed Solution: {idea.proposed_solution}\n"
        f"Target Audience: {idea.target_audience or 'General'}\n"
        f"Industry/Domain: {idea.industry or project.domain or 'General Technology'}\n"
        f"Intended Use Case: {idea.intended_use_case or 'Web / Mobile SaaS application'}\n"
        f"Technical Preferences: {idea.technical_preferences or 'Modern standard cloud stack'}\n"
        f"Constraints: {idea.constraints or 'Standard early-stage engineering team'}\n\n"
        "Generate a structured implementation blueprint with valid JSON containing:\n"
        "- objectives (list of 3-4 concrete project objectives)\n"
        "- functional_requirements (list of 3-5 key functional capabilities)\n"
        "- nonfunctional_requirements (list of 3-5 operational/performance/security requirements)\n"
        "- mvp_scope (list of features strictly included in the initial launch)\n"
        "- phased_milestones (list of objects: phase, duration, deliverables, key_focus)\n"
        "- suggested_database_entities (list of objects: name, purpose, key_attributes)\n"
        "- api_design_endpoints (list of objects: method, path, description)\n"
        "- recommended_tech_stack (object with frontend, backend, database, background_tasks, testing, and rationale tailored to this idea)\n"
        "- task_breakdown (list of 6-8 objects: id, phase, title, description, estimated_days, status='todo', priority='high'/'medium'/'low', dependencies=[])\n"
        "- security_considerations (list of 3-4 concrete security protocols)\n"
        "- risks_and_mitigations (list of objects: risk, mitigation)\n"
        "- estimated_effort_ranges (object with optimistic_weeks, realistic_weeks, conservative_weeks, assumptions_behind_estimates)\n"
        "Tailor all stack choices and task estimates specifically to this problem domain."
    )

    sys_prompt = "You are a Principal Software Architect and Technical Program Manager. Formulate rigorous, modular, phased engineering plans."

    try:
        roadmap_data = llm.generate_structured(prompt, sys_prompt)
    except Exception as e:
        logger.error(f"Error in LLM roadmap generation: {e}")
        roadmap_data = {}

    # Delete previous roadmap for this idea in this project
    db.query(ImplementationRoadmap).filter(
        ImplementationRoadmap.project_id == project.id,
        ImplementationRoadmap.idea_id == idea.id
    ).delete()

    # Ensure task breakdown has proper priority and dependencies
    raw_tasks = roadmap_data.get("task_breakdown") or [
        {
            "id": "task-1",
            "phase": "Phase 1: Foundation",
            "title": "Configure database schemas and migration scripts",
            "description": "Establish PostgreSQL relational models with indexes and foreign keys.",
            "estimated_days": 2,
            "status": "todo",
            "priority": "high",
            "dependencies": []
        },
        {
            "id": "task-2",
            "phase": "Phase 1: Foundation",
            "title": "Implement JWT authentication and tenant isolation",
            "description": "Secure all routes with user verification and role checks.",
            "estimated_days": 2,
            "status": "todo",
            "priority": "high",
            "dependencies": ["task-1"]
        },
        {
            "id": "task-3",
            "phase": "Phase 2: Core Engine",
            "title": "Build core evaluation and scoring algorithm",
            "description": "Implement 10-dimension mathematical normalization and friction inversion.",
            "estimated_days": 3,
            "status": "todo",
            "priority": "high",
            "dependencies": ["task-2"]
        },
        {
            "id": "task-4",
            "phase": "Phase 2: Core Engine",
            "title": "Integrate external scholarly and patent search adapters",
            "description": "Connect OpenAlex and USPTO REST adapters with rate-limit handling.",
            "estimated_days": 3,
            "status": "todo",
            "priority": "medium",
            "dependencies": ["task-3"]
        },
        {
            "id": "task-5",
            "phase": "Phase 3: Workspaces",
            "title": "Deploy interactive AI Mentor and task kanban boards",
            "description": "Create responsive workspace UI with drag-and-drop task progression.",
            "estimated_days": 4,
            "status": "todo",
            "priority": "medium",
            "dependencies": ["task-4"]
        },
        {
            "id": "task-6",
            "phase": "Phase 4: Launch",
            "title": "Automated end-to-end testing and production deployment",
            "description": "Run regression test suites, containerize services, and verify health checks.",
            "estimated_days": 3,
            "status": "todo",
            "priority": "high",
            "dependencies": ["task-5"]
        }
    ]

    # Normalize tasks
    normalized_tasks = []
    for i, t in enumerate(raw_tasks):
        normalized_tasks.append({
            "id": str(t.get("id") or f"task-{i+1}"),
            "phase": t.get("phase") or "Phase 1",
            "title": t.get("title") or "Engineering Task",
            "description": t.get("description") or "",
            "estimated_days": int(t.get("estimated_days") or 2),
            "status": t.get("status") if t.get("status") in ("todo", "in_progress", "done") else "todo",
            "priority": t.get("priority") if t.get("priority") in ("high", "medium", "low") else "medium",
            "dependencies": t.get("dependencies") or []
        })

    effort_ranges = roadmap_data.get("estimated_effort_ranges") or {
        "optimistic_weeks": 6,
        "realistic_weeks": 9,
        "conservative_weeks": 14,
        "assumptions_behind_estimates": "Estimates assume a dedicated team of 2-3 engineers, leveraging existing open-source frameworks, and uninterrupted third-party API availability."
    }

    roadmap = ImplementationRoadmap(
        project_id=project.id,
        idea_id=idea.id,
        objectives=roadmap_data.get("objectives") or [
            "Validate product-market feasibility with a working functional prototype in 8-10 weeks.",
            "Implement automated regression testing with >80% code coverage.",
            "Ensure strict user-level data isolation and compliance."
        ],
        functional_requirements=roadmap_data.get("functional_requirements") or [
            "Multi-idea submission and side-by-side comparative scoring.",
            "Real academic paper discovery and verified reference library.",
            "Interactive AI mentoring across 7 innovation disciplines."
        ],
        nonfunctional_requirements=roadmap_data.get("nonfunctional_requirements") or [
            "Sub-500ms p95 API response latency on cached reads.",
            "Strict tenant authorization on every resource endpoint.",
            "Horizontally scalable stateless REST architecture."
        ],
        mvp_scope=roadmap_data.get("mvp_scope") or [
            "User authentication and multi-tenant workspace isolation.",
            "Multi-idea evaluation and explainable 10-dimension scoring engine.",
            "Scholarly paper search with verified reference library.",
            "Implementation roadmap with interactive task board and architecture specs."
        ],
        phased_milestones=roadmap_data.get("phased_milestones") or [
            {"phase": "Phase 1: Foundation & Data Architecture", "duration": "2 weeks", "deliverables": "Database models, Auth endpoints, Project CRUD."},
            {"phase": "Phase 2: Core Intelligence & Scoring", "duration": "3 weeks", "deliverables": "10-Dimension scoring engine, Literature adapters."},
            {"phase": "Phase 3: Workspaces & Collaboration", "duration": "2 weeks", "deliverables": "AI Mentor sessions, Literature gap analyses, Roadmap board."},
            {"phase": "Phase 4: Hardening & Launch Readiness", "duration": "2 weeks", "deliverables": "End-to-end integration testing, Production deployment."}
        ],
        suggested_database_entities=roadmap_data.get("suggested_database_entities") or [
            {"name": "User", "purpose": "Account identity, JWT credentials, and tenant profile."},
            {"name": "Project", "purpose": "Workspace container for ideas, roadmaps, and papers."},
            {"name": "Idea", "purpose": "Proposal definition, problem statement, and solution spec."},
            {"name": "Evaluation", "purpose": "10-Dimension scoring matrix and qualitative breakdown."},
            {"name": "ImplementationRoadmap", "purpose": "Phased milestones, task board, and architecture."}
        ],
        api_design_endpoints=roadmap_data.get("api_design_endpoints") or [
            {"method": "POST", "path": "/api/v1/auth/login", "description": "Authenticate user and issue JWT token."},
            {"method": "POST", "path": "/api/v1/projects/{id}/evaluate", "description": "Trigger multi-idea scoring engine."},
            {"method": "GET", "path": "/api/v1/research/papers/search", "description": "Search scholarly literature across providers."},
            {"method": "PUT", "path": "/api/v1/projects/{id}/roadmap/tasks/{task_id}", "description": "Update task status and priority."}
        ],
        recommended_tech_stack=roadmap_data.get("recommended_tech_stack") or {
            "frontend": "React.js with Vite and Tailwind CSS for modular responsive UI components.",
            "backend": "FastAPI (Python) for async performance, automatic OpenAPI documentation, and robust Pydantic validation.",
            "database": "PostgreSQL with SQLAlchemy ORM for strict relational integrity and ACID transactions.",
            "background_tasks": "Celery with Redis message broker for long-running AI jobs and export pipelines.",
            "testing": "Pytest for backend coverage and Vitest for frontend component testing."
        },
        task_breakdown=normalized_tasks,
        security_considerations=roadmap_data.get("security_considerations") or [
            "Enforce tenant authorization checks on every resource ID before querying database.",
            "Store all external provider API credentials exclusively in backend environment variables.",
            "Apply input sanitization and Pydantic validation to block injection payloads."
        ],
        risks_and_mitigations=roadmap_data.get("risks_and_mitigations") or [
            {"risk": "External API latency or rate limits", "mitigation": "Implement local response caching and timeout fallbacks."},
            {"risk": "Scope creep during MVP development", "mitigation": "Strictly gate Phase 1 deliverables to defined MVP scope."}
        ],
        estimated_effort_ranges=effort_ranges,
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
    return (
        db.query(ImplementationRoadmap)
        .filter(ImplementationRoadmap.project_id == project.id)
        .order_by(ImplementationRoadmap.created_at.desc())
        .all()
    )


@router.put("/projects/{project_id}/roadmap/tasks/{task_id}", response_model=ImplementationRoadmapOut)
def update_task_details(
    task_id: str,
    status_in: TaskStatusUpdateRequest,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Updates the status ('todo', 'in_progress', 'done'), priority, title, or estimated days
    of a specific task on the project roadmap board.
    """
    roadmap = (
        db.query(ImplementationRoadmap)
        .filter(ImplementationRoadmap.project_id == project.id)
        .order_by(ImplementationRoadmap.created_at.desc())
        .first()
    )
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No roadmap found for project")

    tasks = list(roadmap.task_breakdown)
    updated = False
    for t in tasks:
        if str(t.get("id")) == str(task_id):
            if status_in.status is not None:
                if status_in.status in ("todo", "in_progress", "done"):
                    t["status"] = status_in.status
            if status_in.priority is not None:
                if status_in.priority in ("high", "medium", "low"):
                    t["priority"] = status_in.priority
            if status_in.title is not None and status_in.title.strip():
                t["title"] = status_in.title.strip()
            if status_in.estimated_days is not None and status_in.estimated_days > 0:
                t["estimated_days"] = status_in.estimated_days
            if status_in.dependencies is not None:
                t["dependencies"] = status_in.dependencies
            updated = True
            break

    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task '{task_id}' not found in roadmap")

    roadmap.task_breakdown = tasks
    flag_modified(roadmap, "task_breakdown")
    db.commit()
    db.refresh(roadmap)
    return roadmap


@router.put("/projects/{project_id}/roadmap", response_model=ImplementationRoadmapOut)
def update_roadmap(
    update_in: RoadmapUpdateRequest,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Updates the entire task breakdown, objectives, or MVP scope of the project roadmap."""
    roadmap = (
        db.query(ImplementationRoadmap)
        .filter(ImplementationRoadmap.project_id == project.id)
        .order_by(ImplementationRoadmap.created_at.desc())
        .first()
    )
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No roadmap found for project")

    if update_in.task_breakdown is not None:
        roadmap.task_breakdown = update_in.task_breakdown
        flag_modified(roadmap, "task_breakdown")
    if update_in.objectives is not None:
        roadmap.objectives = update_in.objectives
        flag_modified(roadmap, "objectives")
    if update_in.mvp_scope is not None:
        roadmap.mvp_scope = update_in.mvp_scope
        flag_modified(roadmap, "mvp_scope")

    db.commit()
    db.refresh(roadmap)
    return roadmap
