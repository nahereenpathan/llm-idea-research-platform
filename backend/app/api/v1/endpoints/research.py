import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.project import Project
from app.models.paper import AcademicPaper
from app.models.patent import PatentRecord
from app.models.user import User
from app.schemas.paper import (
    AcademicPaperCreate,
    AcademicPaperUpdate,
    AcademicPaperOut,
    ResearchSourceInfo,
    PaperSearchResponse
)
from app.schemas.patent import (
    PatentRecordCreate,
    PatentRecordUpdate,
    PatentRecordOut,
    PatentSourceInfo,
    PatentSearchResponse
)
from app.api.v1.deps import verify_project_ownership, get_current_user
from app.services.research.openalex_adapter import OpenAlexAdapter
from app.services.research.crossref_adapter import CrossrefAdapter
from app.services.research.ieee_adapter import IEEEAdapter
from app.services.research.uspto_adapter import USPTOAdapter
from app.services.research.epo_adapter import EPOAdapter
from app.services.research.exceptions import (
    ResearchProviderError,
    ProviderNotConfiguredException,
    ProviderRateLimitError,
    ProviderTimeoutError
)
from app.services.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Academic Papers Provider Sources & Search
# ============================================================================

@router.get("/papers/sources", response_model=List[ResearchSourceInfo])
def get_paper_sources():
    """Returns available scholarly metadata providers and their configuration status."""
    ieee_configured = bool(settings.IEEE_API_KEY and settings.IEEE_API_KEY.strip())
    return [
        ResearchSourceInfo(
            id="openalex",
            name="OpenAlex",
            requires_key=False,
            is_configured=True,
            status="active",
            description="Global index of 250M+ scholarly works, authors, and citation graphs. Fully active without credentials."
        ),
        ResearchSourceInfo(
            id="crossref",
            name="Crossref",
            requires_key=False,
            is_configured=True,
            status="active",
            description="Official DOI registry for 150M+ scholarly records and publisher metadata. Fully active without credentials."
        ),
        ResearchSourceInfo(
            id="ieee",
            name="IEEE Xplore",
            requires_key=True,
            is_configured=ieee_configured,
            status="active" if ieee_configured else "unconfigured",
            description="Technical engineering and computer science literature. Requires IEEE_API_KEY in backend/.env."
        )
    ]


@router.get("/papers/search", response_model=PaperSearchResponse)
def search_academic_papers(
    query: str = Query(..., min_length=2, description="Keywords, DOI, author name, or paper title"),
    source: str = Query("openalex", pattern="^(openalex|crossref|ieee)$"),
    search_type: str = Query("keyword", pattern="^(keyword|title|author|doi)$"),
    year_from: Optional[int] = Query(None, ge=1800, le=2100),
    year_to: Optional[int] = Query(None, ge=1800, le=2100),
    page: int = Query(1, ge=1, le=100),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Searches real academic metadata providers (OpenAlex, Crossref, IEEE Xplore).
    Returns verified titles, authors, DOIs, publication years, citations, and abstracts when available.
    """
    if source == "crossref":
        adapter = CrossrefAdapter()
    elif source == "ieee":
        adapter = IEEEAdapter()
    else:
        adapter = OpenAlexAdapter()

    if not adapter.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{source}' is not configured with required API credentials in backend/.env."
        )

    try:
        results_data = adapter.search_papers(
            query=query,
            year_from=year_from,
            year_to=year_to,
            search_type=search_type,
            page=page,
            limit=limit
        )
        return results_data
    except ProviderNotConfiguredException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
    except ProviderRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=e.message)
    except ProviderTimeoutError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=e.message)
    except ResearchProviderError as e:
        raise HTTPException(status_code=e.status_code or status.HTTP_502_BAD_GATEWAY, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in paper search: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Search failed due to unexpected error.")


@router.get("/papers/{paper_id}", response_model=AcademicPaperOut)
def get_paper_details(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full bibliographic metadata for a saved paper in the user's project library."""
    paper = db.query(AcademicPaper).filter(AcademicPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    project = db.query(Project).filter(Project.id == paper.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return paper


@router.post("/projects/{project_id}/papers/save", response_model=AcademicPaperOut, status_code=status.HTTP_201_CREATED)
def save_paper_to_library(
    paper_in: AcademicPaperCreate,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Saves a discovered research paper to the project reference library.
    Enforces duplicate prevention: rejects if paper is already saved in this project.
    """
    # Check for existing paper in this project by external_id, doi, or title
    query_filter = db.query(AcademicPaper).filter(AcademicPaper.project_id == project.id)
    if paper_in.external_id:
        existing = query_filter.filter(AcademicPaper.external_id == paper_in.external_id).first()
    elif paper_in.doi:
        existing = query_filter.filter(AcademicPaper.doi == paper_in.doi).first()
    else:
        existing = query_filter.filter(AcademicPaper.title == paper_in.title).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paper is already saved in this project reference library."
        )

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
    return (
        db.query(AcademicPaper)
        .filter(AcademicPaper.project_id == project.id)
        .order_by(AcademicPaper.created_at.desc())
        .all()
    )


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
    """Generates an AI summary of the paper's abstract, extracting core methods and empirical findings."""
    paper = db.query(AcademicPaper).filter(AcademicPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    project = db.query(Project).filter(Project.id == paper.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if not paper.abstract or "Abstract not provided" in paper.abstract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot summarize paper because publisher metadata did not provide an abstract."
        )

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


# ============================================================================
# Patent Search & Library Endpoints
# ============================================================================

@router.get("/patents/sources", response_model=List[PatentSourceInfo])
def get_patent_sources():
    """Returns available patent search providers and their configuration status."""
    uspto_configured = bool(settings.USPTO_API_KEY and settings.USPTO_API_KEY.strip())
    epo_configured = bool(
        settings.EPO_CONSUMER_KEY and settings.EPO_CONSUMER_KEY.strip()
        and settings.EPO_CONSUMER_SECRET and settings.EPO_CONSUMER_SECRET.strip()
    )
    return [
        PatentSourceInfo(
            id="uspto",
            name="USPTO Open Data Portal",
            requires_key=True,
            is_configured=uspto_configured,
            status="active" if uspto_configured else "unconfigured",
            description="Official US Patent and Trademark Office Open Data Portal API (requires USPTO_API_KEY in backend/.env)."
        ),
        PatentSourceInfo(
            id="epo",
            name="EPO Open Patent Services",
            requires_key=True,
            is_configured=epo_configured,
            status="active" if epo_configured else "unconfigured",
            description="European Patent Office OPS REST API with global coverage (requires EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET in backend/.env)."
        )
    ]


@router.get("/patents/search", response_model=PatentSearchResponse)
def search_patents(
    query: str = Query(..., min_length=2, description="Keywords, technical concept, or patent number"),
    source: str = Query("uspto", pattern="^(uspto|epo)$"),
    search_type: str = Query("keyword", pattern="^(keyword|concept|title|number)$"),
    page: int = Query(1, ge=1, le=100),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Searches official patent registries (USPTO or EPO OPS).
    Includes mandatory epistemic disclaimer: automated searches identify concept overlap
    and do NOT establish legal patentability, infringement status, or freedom-to-operate.
    """
    if source == "epo":
        adapter = EPOAdapter()
    else:
        adapter = USPTOAdapter()

    if not adapter.is_configured():
        if source == "uspto":
            detail_msg = "USPTO Open Data Portal is not configured. Configure USPTO_API_KEY in backend/.env. OpenAlex and Crossref academic paper searches are active without keys."
        else:
            detail_msg = "European Patent Office (EPO OPS) is not configured. Configure EPO_CONSUMER_KEY and EPO_CONSUMER_SECRET in backend/.env."
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail_msg)

    try:
        return adapter.search_patents(query=query, search_type=search_type, page=page, limit=limit)
    except ProviderNotConfiguredException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message)
    except ProviderRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=e.message)
    except ProviderTimeoutError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=e.message)
    except ResearchProviderError as e:
        raise HTTPException(status_code=e.status_code or status.HTTP_502_BAD_GATEWAY, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in patent search: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Patent search failed due to unexpected error.")


@router.get("/patents/{patent_id}", response_model=PatentRecordOut)
def get_patent_details(
    patent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves full metadata for a saved patent record in the user's project library."""
    patent = db.query(PatentRecord).filter(PatentRecord.id == patent_id).first()
    if not patent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patent record not found")

    project = db.query(Project).filter(Project.id == patent.project_id).first()
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return patent


@router.post("/projects/{project_id}/patents/save", response_model=PatentRecordOut, status_code=status.HTTP_201_CREATED)
def save_patent_to_project(
    patent_in: PatentRecordCreate,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Saves a patent record to the project reference library.
    Enforces duplicate prevention: rejects if patent_number is already saved for this project.
    """
    existing = db.query(PatentRecord).filter(
        PatentRecord.project_id == project.id,
        PatentRecord.patent_number == patent_in.patent_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patent '{patent_in.patent_number}' is already saved in this project reference library."
        )

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
    return (
        db.query(PatentRecord)
        .filter(PatentRecord.project_id == project.id)
        .order_by(PatentRecord.created_at.desc())
        .all()
    )


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
