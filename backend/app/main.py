import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
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
    # Startup validation
    logger.info(f"Initializing IdeaLens backend in [{settings.ENVIRONMENT.upper()}] mode...")
    
    # Production safeguards
    if settings.ENVIRONMENT.lower() == "production":
        if settings.DATABASE_URL.startswith("sqlite"):
            raise RuntimeError(
                "CRITICAL: Production deployment cannot run on SQLite. "
                "Configure a valid PostgreSQL connection string in DATABASE_URL."
            )
        insecure_keys = ["change_in_production", "change_me", "idealens_super_secret", "development", "secret"]
        if any(k in settings.SECRET_KEY.lower() for k in insecure_keys) or len(settings.SECRET_KEY) < 32:
            raise RuntimeError(
                "CRITICAL SECURITY ERROR: Default or weak SECRET_KEY detected in production. "
                "Set a unique 256-bit cryptographic secret (e.g. 'openssl rand -hex 32') in environment variables."
            )
        logger.info("Production environment verified: PostgreSQL configured and secure SECRET_KEY active.")
    else:
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
    docs_url=f"{settings.API_V1_STR}/docs" if settings.ENVIRONMENT.lower() != "production" else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.ENVIRONMENT.lower() != "production" else None,
    lifespan=lifespan
)

# Request size limiter middleware
@app.middleware("http")
async def limit_request_size_middleware(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.MAX_REQUEST_SIZE_BYTES:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": f"Request body exceeds maximum allowed size ({settings.MAX_REQUEST_SIZE_BYTES // (1024*1024)}MB)."}
                )
        except ValueError:
            pass
    return await call_next(request)

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
@app.get(f"{settings.API_V1_STR}/health", tags=["Health & Status"])
def health_check(response: Response):
    """System health check verifying database connectivity, environment mode, and engine dialect without credential exposure."""
    db_ok = True
    db_type = engine.dialect.name
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e.__class__.__name__}")
        db_ok = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_ok,
        "database_type": db_type,
        "llm_provider": settings.LLM_PROVIDER
    }


# Request validation exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    msg = first_error.get("msg", "Invalid request parameter")
    if msg.startswith("Value error, "):
        msg = msg[len("Value error, "):]
    loc = first_error.get("loc", [])
    field = loc[-1] if loc else "input"
    field_name = str(field).replace("_", " ").capitalize()
    formatted_msg = f"{field_name}: {msg}" if field and field != "body" else msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": formatted_msg, "errors": errors}
    )


# Global exception handler for safe error reporting
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again or contact support."}
    )

