from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, projects, ideas, evaluation, research,
    gaps, roadmaps, mentor, reports, presentations, exports, jobs
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(ideas.router, tags=["Ideas"])
api_router.include_router(evaluation.router, tags=["Evaluation & Scoring"])
api_router.include_router(research.router, prefix="/research", tags=["Research Engine & Prior Art"])
api_router.include_router(gaps.router, tags=["Research Gap Analysis"])
api_router.include_router(roadmaps.router, tags=["Implementation Roadmaps"])
api_router.include_router(mentor.router, prefix="/mentor", tags=["AI Mentor"])
api_router.include_router(reports.router, tags=["Reports & Documentation"])
api_router.include_router(presentations.router, tags=["Presentation Builder"])
api_router.include_router(exports.router, tags=["Exports & Data Download"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Background Jobs"])
