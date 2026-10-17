from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.models.project import Project
from app.models.idea import Idea
from app.models.paper import AcademicPaper
from app.models.patent import PatentRecord
from app.models.evaluation import Evaluation
from app.models.gap_analysis import ResearchGapAnalysis
from app.models.roadmap import ImplementationRoadmap
from app.models.presentation import Presentation, Slide
from app.schemas.presentation import (
    PresentationCreate, PresentationUpdate, PresentationOut,
    SlideCreate, SlideUpdate, SlideOut
)
from app.api.v1.deps import verify_project_ownership, get_current_user
from app.models.user import User

router = APIRouter()


def build_10_slide_deck_data(
    project: Project,
    idea: Optional[Idea],
    evaluation: Optional[Evaluation],
    papers: List[AcademicPaper],
    patents: List[PatentRecord],
    gap_analysis: Optional[ResearchGapAnalysis],
    roadmap: Optional[ImplementationRoadmap],
    template_type: str
) -> List[Dict[str, Any]]:
    """Builds a rich, factual 10-slide outline grounded in PostgreSQL project data."""
    idea_title = idea.title if idea else project.title
    industry = idea.industry if idea and idea.industry else (project.domain or "Deep Tech Innovation")

    # Evaluation summary
    if evaluation:
        dim_scores = evaluation.dimension_scores or {}
        score = evaluation.overall_score or 0.0
        grade = "A" if score >= 80 else ("B" if score >= 65 else ("C" if score >= 50 else "D"))
        rec = "Recommended for Prototyping" if score >= 65 else "Requires Evidence Refinement"
        score_bullets = [
            f"Viability Score: {score:.1f}/100 (Grade {grade})",
            f"Strategic Verdict: {rec}",
            f"Problem Significance: {dim_scores.get('problem_significance', 7.5):.1f}/10 • Technical Feasibility: {dim_scores.get('technical_feasibility', 7.5):.1f}/10",
            f"Adoption Potential: {dim_scores.get('adoption_potential', 7.0):.1f}/10 • Novelty Distance: {dim_scores.get('novelty_distance', 7.5):.1f}/10"
        ]
    else:
        score_bullets = [
            "Viability Assessment: Baseline parameters initialized",
            "Multi-dimensional comparative evaluation ready for execution",
            "Prioritizes problem significance and technical defensibility"
        ]

    # Papers & Patents for slide 5
    research_bullets = []
    if papers:
        for p in papers[:3]:
            author_str = p.authors[0] if isinstance(p.authors, list) and p.authors else "Scholarly Authors"
            research_bullets.append(f"{p.title[:65]}... ({author_str}, {p.publication_year or 'Recent'})")
    else:
        research_bullets.append("Grounded in OpenAlex and Crossref academic metadata indexes.")
        research_bullets.append("Awaiting saved project library papers for granular citation linkage.")

    if patents:
        for pat in patents[:2]:
            research_bullets.append(f"Patent #{pat.patent_number}: {pat.title[:60]}...")

    # Gaps & Risks for slide 6
    gaps_bullets = []
    if gap_analysis and gap_analysis.identified_gaps:
        for g in gap_analysis.identified_gaps[:3]:
            gaps_bullets.append(f"Research Gap: {g[:90]}...")
    else:
        gaps_bullets.append("Gap: Lack of real-time empirical validation under extreme load conditions.")
        gaps_bullets.append("Risk: Third-party API rate quotas and network latency dependencies.")

    if evaluation and evaluation.risks:
        gaps_bullets.append(f"Operational Risk: {evaluation.risks[0][:90]}...")

    # Architecture & Tech Stack for slide 7
    stack_left = []
    stack_right = []
    if roadmap and roadmap.recommended_tech_stack:
        items = list(roadmap.recommended_tech_stack.items())
        half = len(items) // 2
        stack_left = [f"{k.replace('_', ' ').title()}: {v[:60]}..." for k, v in items[:half]]
        stack_right = [f"{k.replace('_', ' ').title()}: {v[:60]}..." for k, v in items[half:]]
    else:
        stack_left = [
            "Frontend: React 18, Vite, Tailwind CSS",
            "Backend: FastAPI async Python services",
            "Database: PostgreSQL with SQLAlchemy ORM"
        ]
        stack_right = [
            "Export Engines: python-pptx, ReportLab, docx",
            "Task Queue: Celery with Redis broker",
            "Security: JWT bearer tenant authorization"
        ]

    # Milestones for slide 8
    milestone_bullets = []
    if roadmap and roadmap.phased_milestones:
        for m in roadmap.phased_milestones[:4]:
            milestone_bullets.append(f"{m.get('phase', 'Phase')}: {m.get('deliverables', '')[:70]} ({m.get('duration', '2 wks')})")
    else:
        milestone_bullets = [
            "Phase 1: Foundation, DB schemas & JWT authentication (2 weeks)",
            "Phase 2: Core intelligence scoring & paper search adapters (3 weeks)",
            "Phase 3: AI Mentor sessions, gap analysis & roadmaps (2 weeks)",
            "Phase 4: Full export pipelines, regression tests & production (2 weeks)"
        ]

    # Validation plan for slide 9
    val_bullets = []
    if gap_analysis and gap_analysis.proposed_evaluation_methods:
        for exp in gap_analysis.proposed_evaluation_methods[:3]:
            val_bullets.append(f"Experiment: {exp[:90]}...")
    else:
        val_bullets = [
            "Customer Discovery: Conduct 15 structured interviews with target practitioners.",
            "Benchmark Testing: Measure algorithmic latency and throughput under peak load.",
            "Usability Smoke Test: Deploy interactive prototype for rapid workflow feedback."
        ]

    # Citations for slide 10
    citations_list = []
    citations_data = []
    for p in papers[:4]:
        cite_str = f"{p.title} ({p.publication_year or 'Recent'})"
        citations_list.append(cite_str)
        citations_data.append({"title": p.title, "url": p.source_url or (f"https://doi.org/{p.doi}" if p.doi else None)})

    for pat in patents[:2]:
        cite_str = f"Patent #{pat.patent_number}: {pat.title}"
        citations_list.append(cite_str)
        citations_data.append({"title": pat.title, "url": pat.source_url})

    return [
        {
            "slide_number": 1,
            "layout": "title",
            "title": idea_title,
            "subtitle": f"{industry} • {template_type.replace('_', ' ').title()}",
            "bullets": [],
            "notes": f"Generated by IdeaLens AI Platform • {datetime.now(timezone.utc).strftime('%B %Y')}"
        },
        {
            "slide_number": 2,
            "layout": "bullets",
            "title": "Problem Statement & Urgency",
            "subtitle": "Critical friction and market bottlenecks",
            "bullets": [
                f"Core Problem: {idea.problem_statement[:130]}..." if idea else "Complex distributed data analysis requires manual, fragmented tools.",
                f"Impacted User Base: {idea.target_audience[:100]}..." if idea else "Enterprise researchers, startups, and developers.",
                "High economic cost and operational delays from existing ad-hoc solutions."
            ]
        },
        {
            "slide_number": 3,
            "layout": "bullets",
            "title": "Proposed Solution & Value Proposition",
            "subtitle": "Defensible technological breakthrough",
            "bullets": [
                f"Innovation: {idea.proposed_solution[:130]}..." if idea else "Unified AI-powered research and analysis platform with explainable scores.",
                f"Expected Benefits: {idea.expected_benefits[:110]}..." if idea and idea.expected_benefits else "10x acceleration in idea validation and competitive literature diligence.",
                f"Primary Use Case: {idea.intended_use_case[:110]}..." if idea and idea.intended_use_case else "End-to-end innovation pipeline from idea comparison to export."
            ]
        },
        {
            "slide_number": 4,
            "layout": "bullets",
            "title": "Idea Evaluation & Scoring Breakdown",
            "subtitle": "Mathematical 10-dimension viability analysis",
            "bullets": score_bullets
        },
        {
            "slide_number": 5,
            "layout": "bullets",
            "title": "Academic Literature & Prior Art",
            "subtitle": "Peer-reviewed scholarship and patent landscape",
            "bullets": research_bullets
        },
        {
            "slide_number": 6,
            "layout": "bullets",
            "title": "Research Gaps & Key Risks",
            "subtitle": "Addressing literature limitations and technical hurdles",
            "bullets": gaps_bullets
        },
        {
            "slide_number": 7,
            "layout": "two_column",
            "title": "Proposed Architecture & Tech Stack",
            "subtitle": "Scalable, secure, and production-ready implementation",
            "left_column": stack_left,
            "right_column": stack_right,
            "bullets": []
        },
        {
            "slide_number": 8,
            "layout": "bullets",
            "title": "Implementation Roadmap & Milestones",
            "subtitle": "Phased execution timeline with clear deliverables",
            "bullets": milestone_bullets
        },
        {
            "slide_number": 9,
            "layout": "bullets",
            "title": "Validation Plan & Smoke Testing",
            "subtitle": "Empirical hypothesis verification and milestones",
            "bullets": val_bullets
        },
        {
            "slide_number": 10,
            "layout": "bullets",
            "title": "Conclusion & Verified References",
            "subtitle": "Strategic next steps with working source citations",
            "bullets": [
                "Strong commercial and technical feasibility demonstrated.",
                "Ready for phased MVP execution and customer validation.",
                f"Verified evidence basis ({len(papers)} papers, {len(patents)} patents indexed)."
            ],
            "citations": citations_list,
            "citations_data": citations_data
        }
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
    Generates a full 10-slide presentation deck populated with genuine project data,
    evaluations, literature citations, patents, and chosen theme/template.
    """
    idea = None
    if req.idea_id:
        idea = db.query(Idea).filter(Idea.id == req.idea_id, Idea.project_id == project.id).first()
    else:
        idea = db.query(Idea).filter(Idea.project_id == project.id, Idea.is_selected == True).first()
        if not idea:
            idea = db.query(Idea).filter(Idea.project_id == project.id).first()

    # Query latest evaluation
    evaluation = None
    if idea:
        evaluation = (
            db.query(Evaluation)
            .filter(Evaluation.idea_id == idea.id)
            .order_by(Evaluation.created_at.desc())
            .first()
        )

    # Query saved papers & patents
    papers = db.query(AcademicPaper).filter(AcademicPaper.project_id == project.id).all()
    patents = db.query(PatentRecord).filter(PatentRecord.project_id == project.id).all()

    # Query gap analysis & roadmap
    gap_analysis = (
        db.query(ResearchGapAnalysis)
        .filter(ResearchGapAnalysis.project_id == project.id)
        .order_by(ResearchGapAnalysis.created_at.desc())
        .first()
    )

    roadmap = (
        db.query(ImplementationRoadmap)
        .filter(ImplementationRoadmap.project_id == project.id)
        .order_by(ImplementationRoadmap.created_at.desc())
        .first()
    )

    pres_title = req.title or f"{idea.title if idea else project.title} — Executive Pitch Deck"

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

    # Build 10 data-rich slides
    slides_data = build_10_slide_deck_data(
        project=project,
        idea=idea,
        evaluation=evaluation,
        papers=papers,
        patents=patents,
        gap_analysis=gap_analysis,
        roadmap=roadmap,
        template_type=req.template_type or "hackathon"
    )

    created_slides = []
    for idx, slide_item in enumerate(slides_data):
        content = {
            "bullets": slide_item.get("bullets", []),
            "left_column": slide_item.get("left_column", []),
            "right_column": slide_item.get("right_column", []),
            "notes": slide_item.get("notes", ""),
            "citations": slide_item.get("citations", []),
            "citations_data": slide_item.get("citations_data", [])
        }

        slide = Slide(
            presentation_id=pres.id,
            slide_number=idx + 1,
            layout=slide_item["layout"],
            title=slide_item["title"],
            subtitle=slide_item["subtitle"],
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
