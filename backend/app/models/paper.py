from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class AcademicPaper(Base):
    __tablename__ = "academic_papers"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id = Column(String(255), index=True, nullable=True)
    source = Column(String(50), default="openalex", nullable=False)  # openalex, crossref, etc.
    title = Column(Text, nullable=False)
    authors = Column(JSON, default=list, nullable=False)
    publication_year = Column(Integer, nullable=True)
    publication_date = Column(String(50), nullable=True)
    abstract = Column(Text, nullable=True)
    doi = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)
    citation_count = Column(Integer, default=0, nullable=False)
    is_saved_to_library = Column(Boolean, default=False, nullable=False)
    user_notes = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="papers")
