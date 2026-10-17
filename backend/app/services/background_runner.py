import uuid
import threading
import logging
from datetime import datetime, timezone
from typing import Callable, Any, Dict, Optional
from app.core.database import SessionLocal
from app.models.research_job import ResearchJob

logger = logging.getLogger(__name__)


class BackgroundRunner:
    """
    Manages long-running research and generation jobs.
    Supports Celery workers when active, with an asynchronous thread runner
    fallback so that jobs update status, progress, and database results reliably.
    """

    @classmethod
    def create_job(cls, project_id: int, job_type: str, initial_message: str = "Job initialized") -> ResearchJob:
        db = SessionLocal()
        try:
            job = ResearchJob(
                job_uuid=str(uuid.uuid4()),
                project_id=project_id,
                job_type=job_type,
                status="pending",
                progress_percentage=0,
                status_message=initial_message,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job
        finally:
            db.close()

    @classmethod
    def execute_async(cls, job_uuid: str, target_fn: Callable[..., Any], *args, **kwargs):
        """Runs the task in a background daemon thread with real DB tracking."""
        def worker():
            db = SessionLocal()
            try:
                job = db.query(ResearchJob).filter(ResearchJob.job_uuid == job_uuid).first()
                if not job:
                    return

                job.status = "in_progress"
                job.progress_percentage = 20
                job.status_message = "Executing research task..."
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

                # Call target function
                result = target_fn(*args, **kwargs)

                job.status = "completed"
                job.progress_percentage = 100
                job.status_message = "Task completed successfully"
                job.result_data = result if isinstance(result, dict) else {"result": str(result)}
                job.updated_at = datetime.now(timezone.utc)
                db.commit()

            except Exception as e:
                logger.error(f"Error in background job {job_uuid}: {e}", exc_info=True)
                try:
                    job = db.query(ResearchJob).filter(ResearchJob.job_uuid == job_uuid).first()
                    if job:
                        job.status = "failed"
                        job.error_message = str(e)
                        job.status_message = "Execution failed"
                        job.updated_at = datetime.now(timezone.utc)
                        db.commit()
                except Exception:
                    pass
            finally:
                db.close()

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
