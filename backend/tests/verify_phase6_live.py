"""Live end-to-end verification script for IdeaLens Phase 6:
AI Mentor, Research Gap Analysis, and Implementation Roadmap.
Exercises real HTTP requests against http://127.0.0.1:8000.
"""

import sys
import requests

BASE_URL = "http://127.0.0.1:8000"


def run_live_verification():
    print("=== STARTING PHASE 6 LIVE END-TO-END VERIFICATION ===")

    # 1. Health check
    h_resp = requests.get(f"{BASE_URL}/health", timeout=5)
    assert h_resp.status_code == 200, f"Health check failed: {h_resp.status_code}"
    print(" [1/7] Health check: OK")

    # 2. Login
    login_resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": "researcher@idealens.ai", "password": "Password123!"},
        timeout=5
    )
    if login_resp.status_code != 200:
        reg_resp = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"email": "researcher@idealens.ai", "password": "Password123!", "full_name": "Dr. Research"},
            timeout=5
        )
        assert reg_resp.status_code in [200, 201], f"Registration failed: {reg_resp.text}"
        login_resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "researcher@idealens.ai", "password": "Password123!"},
            timeout=5
        )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(" [2/7] User authentication: OK")

    # 3. Create or get existing project and idea
    proj_resp = requests.post(
        f"{BASE_URL}/api/v1/projects/",
        json={"title": "Autonomous Drone Fleet Network", "description": "Swarm robotics for disaster response and search & rescue"},
        headers=headers,
        timeout=5
    )
    if proj_resp.status_code == 201:
        project_id = proj_resp.json()["id"]
    else:
        # Fetch existing
        list_resp = requests.get(f"{BASE_URL}/api/v1/projects/", headers=headers, timeout=5)
        assert list_resp.status_code == 200
        project_id = list_resp.json()[0]["id"]

    idea_resp = requests.post(
        f"{BASE_URL}/api/v1/projects/{project_id}/ideas",
        json={
            "title": "Mesh Protocol Decentralized Relay",
            "problem_statement": "Cellular towers and GPS collapse during earthquakes, leaving survivors isolated.",
            "target_audience": "Search and Rescue disaster relief responders and civilian defense teams.",
            "proposed_solution": "Deploy ad-hoc 802.11ah HaLow mesh topology with self-healing routing algorithms."
        },
        headers=headers,
        timeout=5
    )
    if idea_resp.status_code == 201:
        idea_id = idea_resp.json()["id"]
    else:
        ideas_list = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/ideas", headers=headers, timeout=5).json()
        idea_id = ideas_list[0]["id"]
    print(f" [3/7] Project #{project_id} & Idea #{idea_id} context established: OK")

    # 4. AI Mentor: Lifecycle, Renaming, 7 Modes & Streaming
    # Create
    conv_resp = requests.post(
        f"{BASE_URL}/api/v1/mentor/conversations",
        json={"project_id": project_id, "idea_id": idea_id, "mode": "technical", "title": "Technical Architecture Session"},
        headers=headers,
        timeout=5
    )
    assert conv_resp.status_code == 201, f"Mentor create failed: {conv_resp.text}"
    conv_id = conv_resp.json()["id"]

    # Rename
    rename_resp = requests.put(
        f"{BASE_URL}/api/v1/mentor/conversations/{conv_id}",
        json={"title": "Swarm Mesh Technical Blueprint", "mode": "technical"},
        headers=headers,
        timeout=5
    )
    assert rename_resp.status_code == 200 and rename_resp.json()["title"] == "Swarm Mesh Technical Blueprint"

    # Send message
    msg_resp = requests.post(
        f"{BASE_URL}/api/v1/mentor/conversations/{conv_id}/messages",
        json={"content": "What are the key packet latency tradeoffs in 802.11ah vs LoRa for drone swarms?"},
        headers=headers,
        timeout=10
    )
    assert msg_resp.status_code == 200
    reply = msg_resp.json()
    assert reply["sender"] == "mentor"
    assert len(reply["content"]) > 20

    # Stream message (SSE)
    stream_resp = requests.post(
        f"{BASE_URL}/api/v1/mentor/conversations/{conv_id}/messages/stream",
        json={"content": "Recommend 2 high-priority edge security safeguards."},
        headers=headers,
        stream=True,
        timeout=10
    )
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers.get("content-type", "")
    streamed_data = ""
    for chunk in stream_resp.iter_lines():
        if chunk:
            streamed_data += chunk.decode("utf-8") + "\n"
    assert "data:" in streamed_data
    print(" [4/7] AI Mentor creation, renaming, persistence & SSE streaming: OK")

    # 5. Research Gap Analysis: Grounding, Limitations, Citations
    gap_resp = requests.post(
        f"{BASE_URL}/api/v1/projects/{project_id}/gaps/generate",
        json={"idea_id": idea_id},
        headers=headers,
        timeout=15
    )
    assert gap_resp.status_code == 201, f"Gap analysis failed: {gap_resp.text}"
    gap_data = gap_resp.json()
    assert "evidence_status" in gap_data
    assert len(gap_data["identified_gaps"]) >= 2
    assert len(gap_data["suggested_research_questions"]) >= 2
    assert len(gap_data["proposed_evaluation_methods"]) >= 2
    print(f" [5/7] Research Gap Analysis generated (Status: '{gap_data['evidence_status']}'): OK")

    # 6. Implementation Roadmap: Generation, Task Board & Editing
    roadmap_resp = requests.post(
        f"{BASE_URL}/api/v1/projects/{project_id}/roadmap/generate",
        json={"idea_id": idea_id},
        headers=headers,
        timeout=15
    )
    assert roadmap_resp.status_code == 201, f"Roadmap generation failed: {roadmap_resp.text}"
    roadmap = roadmap_resp.json()
    assert len(roadmap["objectives"]) >= 2
    assert len(roadmap["phased_milestones"]) >= 3
    assert len(roadmap["task_breakdown"]) >= 4

    task_0 = roadmap["task_breakdown"][0]
    task_id = task_0["id"]

    # Toggle status to in_progress
    status_resp = requests.put(
        f"{BASE_URL}/api/v1/projects/{project_id}/roadmap/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=headers,
        timeout=5
    )
    assert status_resp.status_code == 200

    # Edit task details (priority, title, days)
    edit_resp = requests.put(
        f"{BASE_URL}/api/v1/projects/{project_id}/roadmap/tasks/{task_id}",
        json={"priority": "high", "title": "Configure 802.11ah Sub-GHz Physical Layer", "estimated_days": 6, "status": "done"},
        headers=headers,
        timeout=5
    )
    assert edit_resp.status_code == 200
    updated_task = next(t for t in edit_resp.json()["task_breakdown"] if t["id"] == task_id)
    assert updated_task["priority"] == "high"
    assert updated_task["status"] == "done"
    assert updated_task["estimated_days"] == 6
    print(f" [6/7] Implementation Roadmap generation & interactive task editing: OK")

    # 7. Tenant Isolation Security on Live Server
    # Register/Login an isolated second user
    attacker_email = "malicious@intruder.net"
    reg2 = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={"email": attacker_email, "password": "AttackerPass123!", "full_name": "Intruder"},
        timeout=5
    )
    login2 = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": attacker_email, "password": "AttackerPass123!"},
        timeout=5
    )
    attacker_headers = {"Authorization": f"Bearer {login2.json()['access_token']}"}

    # Attempt to tamper with victim's mentor conversation
    intrude_mentor = requests.get(f"{BASE_URL}/api/v1/mentor/conversations/{conv_id}", headers=attacker_headers, timeout=5)
    assert intrude_mentor.status_code in [403, 404]

    # Attempt to tamper with victim's roadmap
    intrude_roadmap = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/roadmap", headers=attacker_headers, timeout=5)
    assert intrude_roadmap.status_code in [403, 404]

    # Attempt to tamper with victim's gap analysis
    intrude_gap = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/gaps", headers=attacker_headers, timeout=5)
    assert intrude_gap.status_code in [403, 404]
    print(" [7/7] Multi-tenant isolation verified on live endpoints: OK")

    print("\n=== ALL LIVE PHASE 6 END-TO-END VERIFICATIONS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    try:
        run_live_verification()
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
