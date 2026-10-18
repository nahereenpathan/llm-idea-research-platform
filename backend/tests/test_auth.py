from app.models.user import User
from app.core.security import get_password_hash


def test_register_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "newuser@idealens.ai",
        "password": "SecurePassword123",
        "full_name": "Test Innovator"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "newuser@idealens.ai"
    assert data["token_type"] == "bearer"
    # Ensure sensitive fields are never leaked
    assert "hashed_password" not in data["user"]
    assert "password" not in data["user"]


def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@idealens.ai",
        "password": "Password123",
        "full_name": "Original"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_case_insensitive_duplicate(client):
    res1 = client.post("/api/v1/auth/register", json={
        "email": "case_test@idealens.ai",
        "password": "Password123",
        "full_name": "Case User"
    })
    assert res1.status_code == 201

    # Attempt registration with uppercase variant
    res2 = client.post("/api/v1/auth/register", json={
        "email": "CASE_TEST@IDEALENS.AI",
        "password": "Password123",
        "full_name": "Case User Upper"
    })
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


def test_register_password_validation(client):
    # Too short (< 6 chars)
    res_short = client.post("/api/v1/auth/register", json={
        "email": "shortpass@idealens.ai",
        "password": "123",
        "full_name": "Short Pass"
    })
    assert res_short.status_code == 400
    assert "at least 6 characters" in res_short.json()["detail"]

    # Too long (> 72 bytes)
    res_long = client.post("/api/v1/auth/register", json={
        "email": "longpass@idealens.ai",
        "password": "A" * 75,
        "full_name": "Long Pass"
    })
    assert res_long.status_code == 400
    assert "72 bytes" in res_long.json()["detail"]


def test_register_invalid_email_format(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "invalid-email-format",
        "password": "ValidPassword123",
        "full_name": "Bad Email"
    })
    assert res.status_code == 422
    assert "detail" in res.json()


def test_login_success_and_failure(client):
    payload = {
        "email": "login_test@idealens.ai",
        "password": "CorrectPassword123",
        "full_name": "Login User"
    }
    client.post("/api/v1/auth/register", json=payload)

    # Valid credentials
    valid_login = client.post("/api/v1/auth/login", json={
        "email": payload["email"],
        "password": "CorrectPassword123"
    })
    assert valid_login.status_code == 200
    data = valid_login.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "hashed_password" not in data["user"]

    # Case-insensitive login email match
    upper_login = client.post("/api/v1/auth/login", json={
        "email": "LOGIN_TEST@IDEALENS.AI",
        "password": "CorrectPassword123"
    })
    assert upper_login.status_code == 200
    assert "access_token" in upper_login.json()

    # Invalid password
    bad_login = client.post("/api/v1/auth/login", json={
        "email": payload["email"],
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]

    # Non-existent user
    nonexistent = client.post("/api/v1/auth/login", json={
        "email": "ghost@idealens.ai",
        "password": "SomePassword123"
    })
    assert nonexistent.status_code == 401


def test_login_inactive_user(client, db):
    # Manually create deactivated user in DB
    deactivated = User(
        email="inactive@idealens.ai",
        hashed_password=get_password_hash("ValidPassword123"),
        full_name="Deactivated Researcher",
        is_active=False
    )
    db.add(deactivated)
    db.commit()

    res = client.post("/api/v1/auth/login", json={
        "email": "inactive@idealens.ai",
        "password": "ValidPassword123"
    })
    assert res.status_code == 400
    assert "deactivated" in res.json()["detail"]


def test_get_current_user_profile(client, auth_headers):
    # Authenticated request
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "researcher@idealens.ai"
    assert data["role"] == "user"
    assert "hashed_password" not in data

    # Missing token
    res_no_token = client.get("/api/v1/auth/me")
    assert res_no_token.status_code == 401

    # Invalid token
    res_bad_token = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad.token.value"})
    assert res_bad_token.status_code == 401
