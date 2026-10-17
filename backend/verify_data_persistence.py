import httpx

def verify_persistence():
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

    # 1. Health check after restart
    h = client.get("/health")
    assert h.status_code == 200, f"Health check failed after restart: {h.text}"
    print("[PASS] 1. Backend server restarted and /health returned 200 OK.")

    # 2. Authenticate existing user created before restart
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "researcher_mvp@idealens.ai",
        "password": "SecurePassword123!"
    })
    assert login_resp.status_code == 200, f"Authentication failed after restart: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 2. User credentials persisted across server restart.")

    # 3. Retrieve project created before restart
    proj_resp = client.get("/api/v1/projects/1", headers=headers)
    assert proj_resp.status_code == 200, f"Project not found after restart: {proj_resp.text}"
    project = proj_resp.json()
    assert project["title"] == "Autonomous Drone Wildfire Early Detection"
    assert project["domain"] == "ClimateTech & Disaster Response"
    assert project["idea_count"] == 3
    print(f"[PASS] 3. Project data persisted across server restart (Title: '{project['title']}').")

    # 4. Retrieve ideas created before restart
    ideas_resp = client.get("/api/v1/projects/1/ideas", headers=headers)
    assert ideas_resp.status_code == 200, f"Ideas not found after restart: {ideas_resp.text}"
    ideas = ideas_resp.json()
    assert len(ideas) == 3, f"Expected 3 ideas, found {len(ideas)}"
    
    titles = [i["title"] for i in ideas]
    print(f"[PASS] 4. All 3 submitted candidate ideas persisted across restart: {titles}")
    
    # Verify selected idea persisted
    selected = [i for i in ideas if i["is_selected"]]
    assert len(selected) == 1 and selected[0]["id"] == 1
    print(f"[PASS] 5. Selected candidate state persisted across restart (Selected Idea: '{selected[0]['title']}').")

    print("\n>>> PERSISTENCE ACROSS RESTART VERIFIED 100%! <<<\n")

if __name__ == "__main__":
    verify_persistence()
