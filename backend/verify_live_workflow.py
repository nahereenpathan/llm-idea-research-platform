import httpx
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_workflow():
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. Health Probe
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    assert health_data["status"] == "healthy"
    assert health_data["database_connected"] is True
    print("[PASS] 1. Live /health endpoint is healthy and database is connected.")

    # 2. Register or Login Test User
    email = "researcher_mvp@idealens.ai"
    password = "SecurePassword123!"
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Dr. Aisha Patel"
    })
    if reg_resp.status_code == 201:
        print("[PASS] 2a. User registered successfully.")
    elif reg_resp.status_code == 400 and "already exists" in reg_resp.text:
        print("[PASS] 2a. User already registered, proceeding to login.")
    else:
        assert False, f"Registration failed: {reg_resp.text}"

    # Login to obtain Bearer token
    login_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 2b. User authenticated and received JWT access token.")

    # 3. Create Project
    proj_payload = {
        "title": "Autonomous Drone Wildfire Early Detection",
        "domain": "ClimateTech & Disaster Response",
        "description": "Evaluating sensor fusion vs edge vision for early-stage wildfire spot detection."
    }
    proj_resp = client.post("/api/v1/projects/", json=proj_payload, headers=headers)
    assert proj_resp.status_code == 201, f"Project creation failed: {proj_resp.text}"
    project = proj_resp.json()
    proj_id = project["id"]
    assert project["title"] == proj_payload["title"]
    print(f"[PASS] 3. Project created successfully (ID: {proj_id}, Title: '{project['title']}').")

    # 4. Test Validation on Invalid Idea Submission
    invalid_idea = {
        "title": "X",  # Too short (min_length=3)
        "problem_statement": "Short",  # Too short (min_length=10)
        "proposed_solution": "Short",  # Too short (min_length=10)
        "target_audience": ""  # Too short (min_length=2)
    }
    val_resp = client.post(f"/api/v1/projects/{proj_id}/ideas", json=invalid_idea, headers=headers)
    assert val_resp.status_code == 422, f"Expected 422 Unprocessable Entity, got {val_resp.status_code}"
    print("[PASS] 4. Input validation rejected underspecified/malformed idea submission with HTTP 422.")

    # 5. Submit 3 Valid Ideas
    ideas_data = [
        {
            "title": "Thermal IR Fleet with LoRa Mesh",
            "problem_statement": "Slow satellite revisitation delays initial wildfire detection by hours, resulting in uncontrolled canopy fires.",
            "proposed_solution": "Deploy autonomous thermal infrared solar drones communicating via subterranean LoRa mesh nodes to stream 5-minute telemetry.",
            "target_audience": "Forest Service agencies, municipal emergency management, wildland firefighters.",
            "industry": "ClimateTech",
            "intended_use_case": "Continuous perimeter surveillance over high-risk timber basins.",
            "expected_benefits": "Detect smoldering lightning strikes within 10 minutes of ignition.",
            "constraints": "Strict FAA remote-ID and battery life in sub-zero ridge temperatures.",
            "estimated_budget": "$15,000 MVP drone prototype",
            "technical_preferences": "LoRaWAN 915MHz, FLIR Boson core, PX4 Autopilot"
        },
        {
            "title": "Acoustic Bio-Sensor Network for Canopy Noise",
            "problem_statement": "Micro-climate turbulence and smoke obfuscation blind thermal optics during overcast inversion layers.",
            "proposed_solution": "Mount distributed solar acoustic sensors in high tree canopies to detect crackling audio signatures using tinyML CNNs.",
            "target_audience": "Conservation park rangers, forestry biologists, county dispatchers.",
            "industry": "Environmental IoT",
            "intended_use_case": "Ground-level smoke-blinded detection under dense old-growth canopy.",
            "expected_benefits": "Zero optical occlusion vulnerability and multi-year battery life.",
            "constraints": "High false positive rate from falling timber and wildlife vocalizations.",
            "estimated_budget": "$8,000 prototype network",
            "technical_preferences": "Edge Impulse, STM32 microcontrollers, MEMS microphones"
        },
        {
            "title": "LEO CubeSat Hyperspectral Alert Gateway",
            "problem_statement": "Terrestrial sensor grids cannot scale across vast boreal wilderness areas without cell or mesh coverage.",
            "proposed_solution": "Utilize existing commercial CubeSat hyperspectral imagery combined with an on-ground edge inference API for automated fire alerts.",
            "target_audience": "Provincial forestry ministries and commercial timber concession operators.",
            "industry": "SpaceTech & GIS",
            "intended_use_case": "Continental-scale early ignition monitoring for unpopulated regions.",
            "expected_benefits": "Global geographic coverage without physical field hardware deployment.",
            "constraints": "Revisit intervals limited to 4-6 hours; cloud cover interference.",
            "estimated_budget": "$25,000 data pipeline MVP",
            "technical_preferences": "Python, GDAL, Sentinel-2 / PlanetScope API, AWS Lambda"
        }
    ]

    submitted_ideas = []
    for idx, idea in enumerate(ideas_data, 1):
        res = client.post(f"/api/v1/projects/{proj_id}/ideas", json=idea, headers=headers)
        assert res.status_code == 201, f"Failed to submit idea {idx}: {res.text}"
        submitted_ideas.append(res.json())
        print(f"[PASS] 5.{idx}. Submitted Candidate Idea #{idx}: '{idea['title']}' (ID: {res.json()['id']}).")

    # 6. Test Enforcing Maximum of 3 Ideas per Project
    fourth_idea = {
        "title": "Excess 4th Candidate Idea",
        "problem_statement": "Testing whether the 3-idea limit is strictly enforced by the backend.",
        "proposed_solution": "Should be rejected with HTTP 400 Bad Request.",
        "target_audience": "Quality assurance and audit testers."
    }
    limit_resp = client.post(f"/api/v1/projects/{proj_id}/ideas", json=fourth_idea, headers=headers)
    assert limit_resp.status_code == 400, f"Expected 400 Bad Request, got {limit_resp.status_code}"
    print(f"[PASS] 6. Enforced maximum of 3 ideas limit: HTTP 400 rejected 4th submission ('{limit_resp.json()['detail']}').")

    # 7. Retrieve Project and Saved Ideas
    get_proj = client.get(f"/api/v1/projects/{proj_id}", headers=headers)
    assert get_proj.status_code == 200
    assert get_proj.json()["idea_count"] == 3
    print(f"[PASS] 7a. Project retrieved: idea_count is {get_proj.json()['idea_count']}.")

    get_ideas = client.get(f"/api/v1/projects/{proj_id}/ideas", headers=headers)
    assert get_ideas.status_code == 200
    retrieved_ideas = get_ideas.json()
    assert len(retrieved_ideas) == 3
    print(f"[PASS] 7b. Retrieved all {len(retrieved_ideas)} saved candidate ideas from database.")

    # 8. Test Selecting an Idea
    selected_id = retrieved_ideas[0]["id"]
    select_resp = client.post(f"/api/v1/ideas/{selected_id}/select", headers=headers)
    assert select_resp.status_code == 200
    assert select_resp.json()["is_selected"] is True
    print(f"[PASS] 8. Successfully marked idea ID {selected_id} as the active selected idea.")

    print("\n>>> ALL FOUNDATION & MVP WORKFLOW STEPS PASSED SUCCESSFULLY! <<<\n")
    return proj_id

if __name__ == "__main__":
    test_workflow()
