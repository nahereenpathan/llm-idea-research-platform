import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db, engine
from app.api.v1.api_router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("idealens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema is ready
    logger.info("Initializing IdeaLens database tables...")
    init_db()
    logger.info("IdeaLens backend started successfully.")
    yield
    # Shutdown
    logger.info("IdeaLens backend shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="IdeaLens — Unified AI Idea Research & Analysis Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Versioned API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health & Status"])
def health_check():
    """System health check verifying database and service readiness."""
    db_ok = True
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e}")
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database_connected": db_ok,
        "llm_provider": settings.LLM_PROVIDER
    }


# Global exception handler for safe error reporting
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again or contact support."}
    )
