import io
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.report import Report
from app.models.presentation import Presentation, Slide
from app.models.idea import Idea
from app.models.evaluation import Evaluation
from app.models.paper import AcademicPaper
from app.models.patent import PatentRecord
from app.models.gap_analysis import ResearchGapAnalysis
from app.models.roadmap import ImplementationRoadmap
from app.api.v1.deps import get_current_user, verify_project_ownership
from app.services.document_generator import DocumentGenerator
from app.services.pptx_generator import PPTXGenerator

router = APIRouter()


@router.get("/reports/{report_id}/export")
def export_report_file(
    report_id: int,
    format: str = Query("pdf", pattern="^(pdf|docx|md|latex)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exports a structured report in the requested file format:
    - pdf: Styled PDF document
    - docx: Microsoft Word document
    - md: Raw GitHub-flavored Markdown
    - latex: Formal LaTeX article document
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    project = db.query(Project).filter(Project.id == report.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    clean_name = "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in report.title])

    if format == "md":
        content = DocumentGenerator.to_markdown(report)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{clean_name}.md"'}
        )

    elif format == "latex":
        content = DocumentGenerator.to_latex(report)
        return Response(
            content=content,
            media_type="application/x-latex",
            headers={"Content-Disposition": f'attachment; filename="{clean_name}.tex"'}
        )

    elif format == "docx":
        buffer = DocumentGenerator.to_docx_buffer(report)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{clean_name}.docx"'}
        )

    elif format == "pdf":
        buffer = DocumentGenerator.to_pdf_buffer(report)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{clean_name}.pdf"'}
        )


@router.get("/presentations/{presentation_id}/export")
def export_presentation_file(
    presentation_id: int,
    format: str = Query("pptx", pattern="^(pptx)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exports the PowerPoint presentation deck as an editable Microsoft PowerPoint (.pptx) file.
    """
    pres = db.query(Presentation).filter(Presentation.id == presentation_id).first()
    if not pres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presentation not found")

    project = db.query(Project).filter(Project.id == pres.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    slides = db.query(Slide).filter(Slide.presentation_id == pres.id).order_by(Slide.sort_order.asc()).all()
    buffer = PPTXGenerator.generate_presentation_buffer(pres, slides)

    clean_name = "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in pres.title])
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{clean_name}.pptx"'}
    )


@router.get("/projects/{project_id}/export/csv")
def export_project_scores_csv(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Exports a structured CSV of all idea evaluation scores, composite metrics,
    and 10-dimension breakdowns for the project.
    """
    ideas = db.query(Idea).filter(Idea.project_id == project.id).all()
    idea_ids = [i.id for i in ideas]
    evaluations = db.query(Evaluation).filter(Evaluation.idea_id.in_(idea_ids)).all() if idea_ids else []

    buffer = DocumentGenerator.to_evaluation_csv_buffer(project, ideas, evaluations)
    clean_name = "".join([c if c.isalnum() or c in ("-", "_") else "_" for c in project.title])
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{clean_name}_evaluation_scores.csv"'}
    )


@router.get("/projects/{project_id}/export-all")
def export_all_project_data(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Exports a comprehensive JSON archive containing all user-owned project records:
    ideas, evaluations, saved scholarly literature, patent records, gap analyses, and roadmaps.
    """
    ideas = db.query(Idea).filter(Idea.project_id == project.id).all()
    papers = db.query(AcademicPaper).filter(AcademicPaper.project_id == project.id).all()
    patents = db.query(PatentRecord).filter(PatentRecord.project_id == project.id).all()
    reports = db.query(Report).filter(Report.project_id == project.id).all()
    roadmaps = db.query(ImplementationRoadmap).filter(ImplementationRoadmap.project_id == project.id).all()

    bundle = {
        "export_timestamp": project.updated_at.isoformat(),
        "platform": "IdeaLens AI Idea Research & Analysis Platform",
        "project": {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "domain": project.domain,
            "created_at": project.created_at.isoformat()
        },
        "ideas": [
            {
                "id": i.id,
                "title": i.title,
                "problem_statement": i.problem_statement,
                "proposed_solution": i.proposed_solution,
                "target_audience": i.target_audience,
                "industry": i.industry,
                "is_selected": i.is_selected
            }
            for i in ideas
        ],
        "academic_papers": [
            {
                "id": p.id,
                "title": p.title,
                "authors": p.authors,
                "publication_year": p.publication_year,
                "doi": p.doi,
                "source_url": p.source_url,
                "user_notes": p.user_notes
            }
            for p in papers
        ],
        "patents": [
            {
                "patent_number": pat.patent_number,
                "title": pat.title,
                "inventors": pat.inventors,
                "source_url": pat.source_url
            }
            for pat in patents
        ],
        "reports": [
            {
                "title": r.title,
                "report_type": r.report_type,
                "content_markdown": r.content_markdown
            }
            for r in reports
        ],
        "roadmaps": [
            {
                "objectives": rm.objectives,
                "recommended_tech_stack": rm.recommended_tech_stack,
                "task_breakdown": rm.task_breakdown
            }
            for rm in roadmaps
        ]
    }
    return bundle
