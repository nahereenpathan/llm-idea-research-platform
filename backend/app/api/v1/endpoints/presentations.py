from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.core.database import get_db
from app.models.project import Project
from app.models.idea import Idea
from app.models.paper import AcademicPaper
from app.models.presentation import Presentation, Slide
from app.schemas.presentation import (
    PresentationCreate, PresentationUpdate, PresentationOut,
    SlideCreate, SlideUpdate, SlideOut
)
from app.api.v1.deps import verify_project_ownership, get_current_user
from app.models.user import User

router = APIRouter()

STANDARD_10_SLIDE_OUTLINES = [
    {"slide_number": 1, "layout": "title", "title": "Project Title", "subtitle": "AI-Powered Innovation & Feasibility Overview", "bullets": []},
    {"slide_number": 2, "layout": "bullets", "title": "The Problem Space", "subtitle": "Urgency and Pain Points", "bullets": ["Critical bottlenecks in existing workflows", "Inefficiencies and manual errors", "High resource overhead"]},
    {"slide_number": 3, "layout": "bullets", "title": "Proposed Solution", "subtitle": "Core Value Proposition", "bullets": ["Automated end-to-end intelligence", "Frictionless multi-step workflows", "Measurable productivity enhancement"]},
    {"slide_number": 4, "layout": "two_column", "title": "Target Users & Demographics", "subtitle": "Who Benefits Most", "bullets": [], "left_column": ["Primary Persona", "Daily pain points", "Job to be done"], "right_column": ["Secondary Beneficiaries", "Enterprise decision makers", "Institutional researchers"]},
    {"slide_number": 5, "layout": "bullets", "title": "Prior Art & Existing Research", "subtitle": "Academic Precedents & Patents", "bullets": ["Scholarly foundational models", "Patent landscape review", "Key literature limitations"]},
    {"slide_number": 6, "layout": "bullets", "title": "Key Differentiation", "subtitle": "Competitive Edge & Defensibility", "bullets": ["Explainable transparent methodology", "Unified multi-source verification", "Zero black-box ambiguity"]},
    {"slide_number": 7, "layout": "two_column", "title": "Technical Architecture", "subtitle": "Stack & Data Flow", "bullets": [], "left_column": ["FastAPI asynchronous backend", "Relational persistence & migrations", "Background job orchestration"], "right_column": ["React modular design system", "Tailwind responsive styling", "Multi-provider LLM abstraction"]},
    {"slide_number": 8, "layout": "bullets", "title": "Implementation Roadmap", "subtitle": "Phased Milestones & MVP", "bullets": ["Phase 1: Architecture & Auth", "Phase 2: Core Analysis Engine", "Phase 3: Workspaces & Mentoring", "Phase 4: Production Exports"]},
    {"slide_number": 9, "layout": "bullets", "title": "Risks & Mitigations", "subtitle": "De-risking the Venture", "bullets": ["API latency -> Local caching & backoff", "Data privacy -> Tenant row-level isolation", "Market adoption -> Rapid user testing"]},
    {"slide_number": 10, "layout": "bullets", "title": "Conclusion & Citations", "subtitle": "Summary & Next Steps", "bullets": ["Ready for rapid prototyping", "Scholarly and patent backing", "Verified validation roadmap"]}
]


@router.get("/projects/{project_id}/presentations", response_model=List[PresentationOut])
def list_project_presentations(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Lists all presentation decks created for the project."""
    presentations = (
        db.query(Presentation)
        .filter(Presentation.project_id == project.id)
        .order_by(Presentation.updated_at.desc())
        .all()
    )
    return presentations


@router.post("/projects/{project_id}/presentations/generate", response_model=PresentationOut, status_code=status.HTTP_201_CREATED)
def generate_presentation(
    req: PresentationCreate,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Generates a full 10-slide presentation deck populated with project data,
    idea details, citations, and chosen theme/template.
    """
    idea = None
    if req.idea_id:
        idea = db.query(Idea).filter(Idea.id == req.idea_id, Idea.project_id == project.id).first()
    else:
        idea = db.query(Idea).filter(Idea.project_id == project.id, Idea.is_selected == True).first()
        if not idea:
            idea = db.query(Idea).filter(Idea.project_id == project.id).first()

    # Saved citations for slide 10
    papers = db.query(AcademicPaper).filter(AcademicPaper.project_id == project.id).limit(3).all()
    citations = [f"{p.title} ({p.publication_year or 'Recent'})" for p in papers]

    pres_title = req.title or f"{idea.title if idea else project.title} - Pitch Deck"

    pres = Presentation(
        project_id=project.id,
        idea_id=idea.id if idea else None,
        title=pres_title,
        theme=req.theme or "navy_modern",
        template_type=req.template_type or "hackathon",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(pres)
    db.commit()
    db.refresh(pres)

    # Populate 10 slides customized with idea specifics
    created_slides = []
    for idx, outline in enumerate(STANDARD_10_SLIDE_OUTLINES):
        title = outline["title"]
        subtitle = outline["subtitle"]
        content = {
            "bullets": list(outline.get("bullets", [])),
            "left_column": list(outline.get("left_column", [])),
            "right_column": list(outline.get("right_column", [])),
            "notes": "",
            "citations": []
        }

        # Inject idea-specific text into standard slides
        if outline["layout"] == "title":
            title = idea.title if idea else project.title
            subtitle = f"{idea.industry if idea else project.domain or 'Innovation'} • {req.template_type.replace('_', ' ').title()}"
        elif outline["slide_number"] == 2 and idea:
            content["bullets"] = [
                idea.problem_statement[:120] + "...",
                f"Impacted Audience: {idea.target_audience}",
                "Existing methods lack real-time transparent validation."
            ]
        elif outline["slide_number"] == 3 and idea:
            content["bullets"] = [
                idea.proposed_solution[:120] + "...",
                f"Key Benefit: {idea.expected_benefits[:100]}...",
                f"Target Use Case: {idea.intended_use_case[:100]}..."
            ]
        elif outline["slide_number"] == 10:
            if citations:
                content["citations"] = citations

        slide = Slide(
            presentation_id=pres.id,
            slide_number=idx + 1,
            layout=outline["layout"],
            title=title,
            subtitle=subtitle,
            content_json=content,
            sort_order=idx
        )
        db.add(slide)
        created_slides.append(slide)

    db.commit()
    db.refresh(pres)
    return pres


@router.get("/presentations/{presentation_id}", response_model=PresentationOut)
def get_presentation(
    presentation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves presentation with all its slides ordered by sort_order."""
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")
    
    project = db.query(Project).filter(Project.id == pres.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return pres


@router.put("/presentations/{presentation_id}", response_model=PresentationOut)
def update_presentation(
    presentation_id: int,
    pres_in: PresentationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates presentation title, theme, or template."""
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")
    
    project = db.query(Project).filter(Project.id == pres.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if pres_in.title is not None:
        pres.title = pres_in.title
    if pres_in.theme is not None:
        pres.theme = pres_in.theme
    if pres_in.template_type is not None:
        pres.template_type = pres_in.template_type

    pres.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(pres)
    return pres


@router.post("/presentations/{presentation_id}/slides", response_model=SlideOut, status_code=status.HTTP_201_CREATED)
def add_slide(
    presentation_id: int,
    slide_in: SlideCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Appends a new slide to the presentation."""
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")
    
    project = db.query(Project).filter(Project.id == pres.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    current_slide_count = db.query(Slide).filter(Slide.presentation_id == pres.id).count()

    slide = Slide(
        presentation_id=pres.id,
        slide_number=slide_in.slide_number or (current_slide_count + 1),
        layout=slide_in.layout or "bullets",
        title=slide_in.title or "New Slide",
        subtitle=slide_in.subtitle,
        content_json=slide_in.content_json or {"bullets": ["Key discussion point"]},
        sort_order=slide_in.sort_order if slide_in.sort_order is not None else current_slide_count
    )
    db.add(slide)
    pres.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(slide)
    return slide


@router.put("/slides/{slide_id}", response_model=SlideOut)
def update_slide(
    slide_id: int,
    slide_in: SlideUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates slide title, subtitle, layout, or bullet content."""
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slide not found")

    pres = db.query(Presentation).filter(Presentation.id == slide.presentation_id).first()
    project = db.query(Project).filter(Project.id == pres.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    for field, val in slide_in.model_dump(exclude_unset=True).items():
        setattr(slide, field, val)

    pres.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(slide)
    return slide


@router.delete("/slides/{slide_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_slide(
    slide_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a slide from the presentation."""
    slide = db.query(Slide).filter(Slide.id == slide_id).first()
    if not slide:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slide not found")

    pres = db.query(Presentation).filter(Presentation.id == slide.presentation_id).first()
    project = db.query(Project).filter(Project.id == pres.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(slide)
    pres.updated_at = datetime.now(timezone.utc)
    db.commit()
    return None


@router.delete("/presentations/{presentation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_presentation(
    presentation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a presentation deck and all its slides."""
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    project = db.query(Project).filter(Project.id == pres.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(pres)
    db.commit()
    return None
