import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Engine configuration with PostgreSQL production pooling and SQLite local support
engine_kwargs = {
    "pool_pre_ping": True,
}

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    # If using relative sqlite path, resolve against the directory where canonical idealens.db resides
    if "./idealens.db" in db_url or db_url.endswith("/idealens.db") or db_url == "sqlite:///idealens.db":
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        canonical_db = os.path.join(backend_dir, "idealens.db")
        if os.path.exists(canonical_db):
            canonical_db_posix = canonical_db.replace("\\", "/")
            db_url = f"sqlite:///{canonical_db_posix}"
else:
    # Production-grade PostgreSQL connection pooling
    engine_kwargs.update({
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
        "pool_recycle": settings.DATABASE_POOL_RECYCLE,
    })

engine = create_engine(
    db_url,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides an active database session for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes tables in database if they do not exist."""
    # Ensure all models are imported so that Base.metadata has all table definitions
    from app.models import (
        user, project, idea, evaluation, paper, patent,
        research_job, gap_analysis, roadmap, mentor, report, presentation
    )
    Base.metadata.create_all(bind=engine)

    # Automatically ensure academic_papers table has any newer columns
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if "academic_papers" in inspector.get_table_names():
            columns = {c["name"] for c in inspector.get_columns("academic_papers")}
            new_columns = [
                ("pdf_url", "TEXT"),
                ("landing_page_url", "TEXT"),
                ("repository_url", "TEXT"),
                ("is_open_access", "BOOLEAN DEFAULT 0"),
                ("open_access_status", "VARCHAR(50)"),
                ("venue", "VARCHAR(255)")
            ]
            with engine.begin() as conn:
                for col_name, col_type in new_columns:
                    if col_name not in columns:
                        conn.execute(text(f"ALTER TABLE academic_papers ADD COLUMN {col_name} {col_type}"))
    except Exception:
        pass
