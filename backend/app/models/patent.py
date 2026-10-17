from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base


class PatentRecord(Base):
    __tablename__ = "patent_records"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    patent_number = Column(String(100), index=True, nullable=False)
    title = Column(Text, nullable=False)
    inventors = Column(JSON, default=list, nullable=False)
    publication_date = Column(String(50), nullable=True)
    filing_date = Column(String(50), nullable=True)
    abstract = Column(Text, nullable=True)
    status = Column(String(50), nullable=True)
    source = Column(String(50), default="uspto", nullable=False)
    source_url = Column(Text, nullable=True)
    is_saved = Column(Boolean, default=False, nullable=False)
    similarity_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="patents")
