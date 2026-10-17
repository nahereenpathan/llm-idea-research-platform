import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Use isolated in-memory or test SQLite database
TEST_DATABASE_URL = "sqlite:///./test_idealens.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_idealens.db"):
        try:
            os.remove("./test_idealens.db")
        except Exception:
            pass


@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Registers and authenticates a test user, returning Bearer auth headers."""
    register_payload = {
        "email": "researcher@idealens.ai",
        "password": "Password123!",
        "full_name": "Dr. Research"
    }
    resp = client.post("/api/v1/auth/register", json=register_payload)
    if resp.status_code == 201:
        token = resp.json()["access_token"]
    else:
        # User might already exist, login instead
        login_resp = client.post("/api/v1/auth/login", json={"email": register_payload["email"], "password": register_payload["password"]})
        token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_headers(client):
    """Registers and authenticates a second isolated user to test tenant isolation."""
    email = "attacker@otherdomain.com"
    pwd = "HackerPassword123!"
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "full_name": "Other User"})
    if resp.status_code == 201:
        token = resp.json()["access_token"]
    else:
        login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
