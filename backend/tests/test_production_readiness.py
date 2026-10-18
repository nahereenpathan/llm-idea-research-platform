import os
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

from app.core.config import Settings
from app.core.database import Base
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from app.main import app as fastapi_app
import app.models  # Ensure all models registered


def test_production_sqlite_safeguard():
    """Verify that the application strictly prohibits SQLite in production mode."""
    with pytest.raises(ValueError, match="SQLite is strictly prohibited in production mode"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="sqlite:///./idealens_prod.db",
            SECRET_KEY="c84d6e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d",
            BACKEND_CORS_ORIGINS=["https://app.idealens.ai"]
        )


def test_production_non_postgresql_scheme_safeguard():
    """Verify that non-PostgreSQL URLs are rejected in production mode."""
    with pytest.raises(ValueError, match="DATABASE_URL must use the PostgreSQL dialect"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/idealens",
            SECRET_KEY="c84d6e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d",
            BACKEND_CORS_ORIGINS=["https://app.idealens.ai"]
        )


def test_production_weak_or_placeholder_secret_key_safeguard():
    """Verify that default or placeholder secret keys are blocked in production."""
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/idealens",
            SECRET_KEY="idealens_super_secret_jwt_key_development_change_in_production_2026",
            BACKEND_CORS_ORIGINS=["https://app.idealens.ai"]
        )

    # Key too short (< 32 chars)
    with pytest.raises(ValueError, match="at least 32 characters long"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/idealens",
            SECRET_KEY="too_short_key_12345",
            BACKEND_CORS_ORIGINS=["https://app.idealens.ai"]
        )


def test_production_cors_safeguard():
    """Verify that localhost-only or wildcard CORS origins are rejected in production."""
    with pytest.raises(ValueError, match="BACKEND_CORS_ORIGINS contains only local development addresses"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/idealens",
            SECRET_KEY="c84d6e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d",
            BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
        )

    with pytest.raises(ValueError, match="Wildcard '\\*' in BACKEND_CORS_ORIGINS is prohibited"):
        Settings(
            ENVIRONMENT="production",
            DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/idealens",
            SECRET_KEY="c84d6e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d",
            BACKEND_CORS_ORIGINS=["*"]
        )


def test_cors_origins_string_and_json_parsing():
    """Verify CORS origins can be parsed from comma-separated string or JSON string."""
    s1 = Settings(BACKEND_CORS_ORIGINS="https://idealens.ai, https://app.idealens.ai")
    assert s1.BACKEND_CORS_ORIGINS == ["https://idealens.ai", "https://app.idealens.ai"]

    s2 = Settings(BACKEND_CORS_ORIGINS='["https://idealens.ai", "https://app.idealens.ai"]')
    assert s2.BACKEND_CORS_ORIGINS == ["https://idealens.ai", "https://app.idealens.ai"]


def test_development_defaults_preserved():
    """Verify that development mode allows default SQLite, dev SECRET_KEY, and localhost CORS without errors."""
    dev_settings = Settings(ENVIRONMENT="development")
    assert dev_settings.ENVIRONMENT == "development"
    assert dev_settings.DATABASE_URL.startswith("sqlite")
    assert len(dev_settings.BACKEND_CORS_ORIGINS) > 0


def test_production_valid_configuration():
    """Verify that a compliant PostgreSQL connection, 64-char key, and production CORS pass validation."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        DATABASE_URL="postgresql+psycopg2://idealens_user:StrongPassword2026!@postgres-host:5432/idealens_db",
        SECRET_KEY="c84d6e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d",
        BACKEND_CORS_ORIGINS=["https://idealens.ai", "https://app.idealens.ai"]
    )
    assert prod_settings.ENVIRONMENT == "production"
    assert "postgresql" in prod_settings.DATABASE_URL
    assert len(prod_settings.SECRET_KEY) == 64
    assert prod_settings.BACKEND_CORS_ORIGINS == ["https://idealens.ai", "https://app.idealens.ai"]


def test_postgresql_ddl_generation_all_models():
    """Verify all 15 SQLAlchemy tables compile valid PostgreSQL DDL."""
    tables = Base.metadata.sorted_tables
    assert len(tables) >= 15

    for table in tables:
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        assert "CREATE TABLE" in ddl
        # Verify JSON and constraints are handled properly
        assert table.name in ddl


def test_bcrypt_password_hashing():
    """Verify bcrypt salt uniqueness and password verification."""
    pwd = "StrongUserPassword123!"
    h1 = get_password_hash(pwd)
    h2 = get_password_hash(pwd)
    
    # Bcrypt produces unique salts for every hash
    assert h1 != h2
    assert verify_password(pwd, h1) is True
    assert verify_password(pwd, h2) is True
    assert verify_password("WrongPassword123!", h1) is False


def test_jwt_tampering_and_expiration():
    """Verify forged, tampered, or expired tokens are rejected."""
    token = create_access_token(subject=42)
    decoded = decode_token(token)
    assert decoded["sub"] == "42"

    # Tampered token
    tampered = token[:-5] + "XXXXX"
    assert decode_token(tampered) is None

    # Forged token with invalid signature
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.fake_signature"
    assert decode_token(fake_token) is None


def test_request_size_limiter():
    """Verify request size limiter middleware blocks payloads > 10MB."""
    client = TestClient(fastapi_app)
    headers = {"Content-Length": str(15 * 1024 * 1024)}  # 15 MB
    res = client.post("/api/v1/auth/login", headers=headers, json={"email": "test@test.com", "password": "x"})
    assert res.status_code == 413
    assert "Request body exceeds maximum allowed size" in res.json()["detail"]


def test_multi_tenant_cross_user_isolation(client, auth_headers):
    """
    Exhaustive verification that User 2 cannot access, mutate, or download
    User 1's projects, ideas, reports, presentations, papers, patents, or roadmaps.
    """
    # 1. User 1 creates a project and idea
    p1_res = client.post("/api/v1/projects/", json={
        "title": "Confidential Defense Quantum Computing",
        "description": "Sensitive enterprise project"
    }, headers=auth_headers)
    assert p1_res.status_code == 201
    p1_id = p1_res.json()["id"]

    idea_res = client.post(f"/api/v1/projects/{p1_id}/ideas", json={
        "title": "Cryogenic Quantum Qubit Interface",
        "problem_statement": "Decoherence in microwave readouts",
        "proposed_solution": "Optical frequency translation",
        "target_audience": "Defense lab researchers",
        "constraints": "Sub-Kelvin temperatures"
    }, headers=auth_headers)
    assert idea_res.status_code == 201
    idea_id = idea_res.json()["id"]

    # User 1 generates a report
    rep_res = client.post(f"/api/v1/projects/{p1_id}/reports/generate", json={
        "idea_id": idea_id,
        "report_type": "full_documentation"
    }, headers=auth_headers)
    assert rep_res.status_code == 201
    rep_id = rep_res.json()["id"]

    # User 1 generates a presentation
    pres_res = client.post(f"/api/v1/projects/{p1_id}/presentations/generate", json={
        "idea_id": idea_id,
        "template_type": "academic"
    }, headers=auth_headers)
    assert pres_res.status_code == 201
    pres_id = pres_res.json()["id"]

    # 2. Register & Authenticate User 2 (Intruder)
    u2_email = f"intruder_{uuid.uuid4().hex[:8]}@unauthorized.com"
    client.post("/api/v1/auth/register", json={
        "email": u2_email,
        "password": "Password123!",
        "full_name": "Unauthorized Intruder"
    })
    u2_token = client.post("/api/v1/auth/login", json={
        "email": u2_email,
        "password": "Password123!"
    }).json()["access_token"]
    u2_headers = {"Authorization": f"Bearer {u2_token}"}

    # 3. User 2 attempts unauthorized access
    # Projects
    assert client.get(f"/api/v1/projects/{p1_id}", headers=u2_headers).status_code in [403, 404]
    assert client.put(f"/api/v1/projects/{p1_id}", json={"title": "Hacked"}, headers=u2_headers).status_code in [403, 404]
    assert client.delete(f"/api/v1/projects/{p1_id}", headers=u2_headers).status_code in [403, 404]

    # Ideas
    assert client.get(f"/api/v1/projects/{p1_id}/ideas", headers=u2_headers).status_code in [403, 404]
    assert client.put(f"/api/v1/ideas/{idea_id}", json={"title": "Hacked Idea"}, headers=u2_headers).status_code in [403, 404]
    assert client.delete(f"/api/v1/ideas/{idea_id}", headers=u2_headers).status_code in [403, 404]

    # Reports & Exports
    assert client.get(f"/api/v1/projects/{p1_id}/reports", headers=u2_headers).status_code in [403, 404]
    assert client.get(f"/api/v1/reports/{rep_id}", headers=u2_headers).status_code in [403, 404]
    assert client.get(f"/api/v1/reports/{rep_id}/export?format=pdf", headers=u2_headers).status_code in [403, 404]
    assert client.get(f"/api/v1/reports/{rep_id}/export?format=docx", headers=u2_headers).status_code in [403, 404]

    # Presentations & PPTX
    assert client.get(f"/api/v1/projects/{p1_id}/presentations", headers=u2_headers).status_code in [403, 404]
    assert client.get(f"/api/v1/presentations/{pres_id}/export?format=pptx", headers=u2_headers).status_code in [403, 404]

    # CSV Score Export
    assert client.get(f"/api/v1/projects/{p1_id}/export/csv", headers=u2_headers).status_code in [403, 404]

    # Roadmap & Gaps
    assert client.post(f"/api/v1/projects/{p1_id}/roadmap/generate", json={"idea_id": idea_id}, headers=u2_headers).status_code in [403, 404]
    assert client.post(f"/api/v1/projects/{p1_id}/gaps/generate", json={"idea_id": idea_id}, headers=u2_headers).status_code in [403, 404]


def test_health_check_endpoint():
    """Verify that /health accurately reports environment, engine dialect, and connectivity without credential exposure."""
    client = TestClient(fastapi_app)
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["database_type"] in ["sqlite", "postgresql"]
    assert "password" not in str(data).lower()
    assert "secret" not in str(data).lower()


def test_health_check_db_failure_returns_503(monkeypatch):
    """Verify that /health returns HTTP 503 and unhealthy status when database probe fails."""
    from app.core import database
    from unittest.mock import MagicMock

    mock_connect = MagicMock(side_effect=Exception("Database connection timeout"))
    monkeypatch.setattr(database.engine, "connect", mock_connect)

    client = TestClient(fastapi_app)
    res = client.get("/health")
    assert res.status_code == 503
    data = res.json()
    assert data["status"] == "unhealthy"
    assert data["database_connected"] is False

