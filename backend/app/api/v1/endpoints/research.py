from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from app.core.database import get_db
from app.models.project import Project
from app.models.paper import AcademicPaper
from app.models.patent import PatentRecord
from app.schemas.paper import AcademicPaperCreate, AcademicPaperUpdate, AcademicPaperOut
from app.schemas.patent import PatentRecordCreate, PatentRecordUpdate, PatentRecordOut
from app.api.v1.deps import verify_project_ownership, get_current_user
from app.models.user import User
from app.services.research.openalex_adapter import OpenAlexAdapter
from app.services.research.crossref_adapter import CrossrefAdapter
from app.services.research.uspto_adapter import USPTOAdapter
from app.services.ai.factory import get_llm_provider

router = APIRouter()


# --- Academic Papers ---

@router.get("/papers/search")
def search_academic_papers(
    query: str = Query(..., min_length=2, description="Keywords or paper title"),
    source: str = Query("openalex", pattern="^(openalex|crossref)$"),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=25),
    current_user: User = Depends(get_current_user)
):
    """
    Searches real scholarly literature using OpenAlex or Crossref APIs.
    Returns live paper metadata with DOIs, authors, citations, and abstracts.
    """
    if source == "crossref":
        adapter = CrossrefAdapter()
    else:
        adapter = OpenAlexAdapter()

    results = adapter.search_papers(query=query, year_from=year_from, year_to=year_to, limit=limit)
    return {"query": query, "source": source, "count": len(results), "results": results}


@router.post("/projects/{project_id}/papers/save", response_model=AcademicPaperOut, status_code=status.HTTP_201_CREATED)
def save_paper_to_library(
    paper_in: AcademicPaperCreate,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Saves a discovered research paper to the project reference library."""
    paper = AcademicPaper(
        project_id=project.id,
        external_id=paper_in.external_id,
        source=paper_in.source,
        title=paper_in.title,
        authors=paper_in.authors,
        publication_year=paper_in.publication_year,
        publication_date=paper_in.publication_date,
        abstract=paper_in.abstract,
        doi=paper_in.doi,
        source_url=paper_in.source_url,
        citation_count=paper_in.citation_count,
        is_saved_to_library=True,
        user_notes=paper_in.user_notes,
        ai_summary=paper_in.ai_summary,
        created_at=datetime.now(timezone.utc)
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    return paper


@router.get("/projects/{project_id}/papers", response_model=List[AcademicPaperOut])
def get_project_papers(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Retrieves all saved academic papers in project library."""
    papers = db.query(AcademicPaper).filter(AcademicPaper.project_id == project.id).order_by(AcademicPaper.created_at.desc()).all()
    return papers


@router.put("/papers/{paper_id}", response_model=AcademicPaperOut)
def update_project_paper(
    paper_id: int,
    paper_in: AcademicPaperUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates user notes or summary on a saved academic paper."""
    paper = db.query(AcademicPaper).filter(AcademicPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    
    project = db.query(Project).filter(Project.id == paper.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if paper_in.user_notes is not None:
        paper.user_notes = paper_in.user_notes
    if paper_in.is_saved_to_library is not None:
        paper.is_saved_to_library = paper_in.is_saved_to_library
    if paper_in.ai_summary is not None:
        paper.ai_summary = paper_in.ai_summary

    db.commit()
    db.refresh(paper)
    return paper


@router.delete("/papers/{paper_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_paper(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a paper from the project library."""
    paper = db.query(AcademicPaper).filter(AcademicPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    project = db.query(Project).filter(Project.id == paper.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(paper)
    db.commit()
    return None


@router.post("/papers/{paper_id}/summarize", response_model=AcademicPaperOut)
def summarize_paper(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates an AI summary of the paper's abstract, extracting core methods and findings."""
    paper = db.query(AcademicPaper).filter(AcademicPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    
    project = db.query(Project).filter(Project.id == paper.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    llm = get_llm_provider()
    prompt = (
        f"Summarize the following scholarly paper abstract:\n"
        f"Title: {paper.title}\n"
        f"Abstract: {paper.abstract}\n\n"
        "Provide a concise 3-4 bullet point synthesis highlighting:\n"
        "- Objective & Proposed Method\n"
        "- Key Empirical Findings\n"
        "- Practical Limitations"
    )
    summary_text = llm.generate_text(prompt, "You are an academic literature synthesis specialist.")
    paper.ai_summary = summary_text
    db.commit()
    db.refresh(paper)
    return paper


# --- Patents ---

@router.get("/patents/search")
def search_patents(
    query: str = Query(..., min_length=2, description="Keywords or technical domain"),
    limit: int = Query(10, ge=1, le=25),
    current_user: User = Depends(get_current_user)
):
    """
    Searches patent databases using USPTO adapter.
    Includes disclaimer: does not replace formal legal counsel.
    """
    adapter = USPTOAdapter()
    results = adapter.search_patents(query=query, limit=limit)
    return {
        "query": query,
        "source": "uspto",
        "count": len(results),
        "disclaimer": "Automated patent searches identify potential prior art and concept similarities but do NOT constitute legal clearance or formal patentability opinions.",
        "results": results
    }


@router.post("/projects/{project_id}/patents/save", response_model=PatentRecordOut, status_code=status.HTTP_201_CREATED)
def save_patent_to_project(
    patent_in: PatentRecordCreate,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Saves a patent record to the project reference library."""
    patent = PatentRecord(
        project_id=project.id,
        patent_number=patent_in.patent_number,
        title=patent_in.title,
        inventors=patent_in.inventors,
        publication_date=patent_in.publication_date,
        filing_date=patent_in.filing_date,
        abstract=patent_in.abstract,
        status=patent_in.status,
        source=patent_in.source,
        source_url=patent_in.source_url,
        is_saved=True,
        similarity_notes=patent_in.similarity_notes,
        created_at=datetime.now(timezone.utc)
    )
    db.add(patent)
    db.commit()
    db.refresh(patent)
    return patent


@router.get("/projects/{project_id}/patents", response_model=List[PatentRecordOut])
def get_project_patents(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Retrieves all saved patent records for project."""
    patents = db.query(PatentRecord).filter(PatentRecord.project_id == project.id).order_by(PatentRecord.created_at.desc()).all()
    return patents


@router.delete("/patents/{patent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_patent(
    patent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Removes a patent record from the project library."""
    patent = db.query(PatentRecord).filter(PatentRecord.id == patent_id).first()
    if not patent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patent not found")

    project = db.query(Project).filter(Project.id == patent.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(patent)
    db.commit()
    return None
