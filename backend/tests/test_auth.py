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
    assert "access_token" in valid_login.json()

    # Invalid password
    bad_login = client.post("/api/v1/auth/login", json={
        "email": payload["email"],
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401


def test_get_current_user_profile(client, auth_headers):
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "researcher@idealens.ai"
    assert data["role"] == "user"
