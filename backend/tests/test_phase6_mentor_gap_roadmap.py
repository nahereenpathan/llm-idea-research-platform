import pytest
from fastapi.testclient import TestClient


def create_test_project_and_idea(client: TestClient, headers: dict):
    proj_resp = client.post(
        "/api/v1/projects/",
        json={"title": "Edge AI IoT Sentinel", "description": "Low-power distributed computer vision on microcontrollers"},
        headers=headers
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    idea_resp = client.post(
        f"/api/v1/projects/{proj_id}/ideas",
        json={
            "title": "Quantized TinyML Anomaly Detector",
            "problem_statement": "High network latency and battery consumption transmitting raw sensor video to cloud servers.",
            "target_audience": "Industrial automation plants and remote wildlife monitoring teams",
            "proposed_solution": "Deploy 4-bit INT quantization CNNs on microcontrollers with on-device flash caching."
        },
        headers=headers
    )
    assert idea_resp.status_code == 201
    idea_id = idea_resp.json()["id"]
    return proj_id, idea_id


def test_mentor_modes_and_conversation_lifecycle(client: TestClient, auth_headers: dict):
    """Verifies conversation creation, renaming, mode switching, messaging, streaming, and deletion."""
    proj_id, idea_id = create_test_project_and_idea(client, auth_headers)

    # 1. Create a conversation in 'technical' mode
    create_payload = {
        "project_id": proj_id,
        "idea_id": idea_id,
        "mode": "technical",
        "title": "Technical Architecture Review"
    }
    create_resp = client.post("/api/v1/mentor/conversations", json=create_payload, headers=auth_headers)
    assert create_resp.status_code == 201
    conv = create_resp.json()
    conv_id = conv["id"]
    assert conv["mode"] == "technical"
    assert conv["title"] == "Technical Architecture Review"
    assert conv["project_id"] == proj_id

    # 2. Rename conversation and switch mode
    update_resp = client.put(
        f"/api/v1/mentor/conversations/{conv_id}",
        json={"title": "Renamed Technical & Validation Session", "mode": "validation"},
        headers=auth_headers
    )
    assert update_resp.status_code == 200
    updated_conv = update_resp.json()
    assert updated_conv["title"] == "Renamed Technical & Validation Session"
    assert updated_conv["mode"] == "validation"

    # 3. Post a message to mentor
    msg_resp = client.post(
        f"/api/v1/mentor/conversations/{conv_id}/messages",
        json={"content": "What are the best lightweight validation experiments to run on microcontrollers?"},
        headers=auth_headers
    )
    assert msg_resp.status_code == 200
    reply = msg_resp.json()
    assert reply["sender"] == "mentor"
    assert len(reply["content"]) > 10

    # 4. Verify conversation detail contains both user and assistant messages
    detail_resp = client.get(f"/api/v1/mentor/conversations/{conv_id}", headers=auth_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["messages"]) >= 2
    assert detail["messages"][-1]["sender"] == "mentor"

    # 5. Test SSE streaming response endpoint
    stream_resp = client.post(
        f"/api/v1/mentor/conversations/{conv_id}/messages/stream",
        json={"content": "Summarize key validation risks in one concise sentence."},
        headers=auth_headers
    )
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    stream_body = stream_resp.text
    assert "data:" in stream_body

    # 6. Delete conversation
    del_resp = client.delete(f"/api/v1/mentor/conversations/{conv_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # 7. Confirm 404 after deletion
    check_resp = client.get(f"/api/v1/mentor/conversations/{conv_id}", headers=auth_headers)
    assert check_resp.status_code == 404


def test_mentor_tenant_isolation(client: TestClient, auth_headers: dict, second_user_headers: dict):
    """Ensures a user cannot view, rename, send messages to, or delete another user's mentor session."""
    # User 1 creates conversation
    create_resp = client.post(
        "/api/v1/mentor/conversations",
        json={"mode": "idea", "title": "Confidential IP Session"},
        headers=auth_headers
    )
    assert create_resp.status_code == 201
    conv_id = create_resp.json()["id"]

    # User 2 attempts to access User 1's conversation
    assert client.get(f"/api/v1/mentor/conversations/{conv_id}", headers=second_user_headers).status_code in [403, 404]
    assert client.put(f"/api/v1/mentor/conversations/{conv_id}", json={"title": "Hacked"}, headers=second_user_headers).status_code in [403, 404]
    assert client.post(f"/api/v1/mentor/conversations/{conv_id}/messages", json={"content": "Steal"}, headers=second_user_headers).status_code in [403, 404]
    assert client.post(f"/api/v1/mentor/conversations/{conv_id}/messages/stream", json={"content": "Steal"}, headers=second_user_headers).status_code in [403, 404]
    assert client.delete(f"/api/v1/mentor/conversations/{conv_id}", headers=second_user_headers).status_code in [403, 404]

    # Verify conversation is intact for User 1
    assert client.get(f"/api/v1/mentor/conversations/{conv_id}", headers=auth_headers).status_code == 200


def test_mentor_all_7_modes(client: TestClient, auth_headers: dict):
    """Verifies that all 7 mentor modes are accepted and function reliably."""
    modes = ["idea", "research", "technical", "product", "business", "validation", "pitch"]
    for mode in modes:
        resp = client.post(
            "/api/v1/mentor/conversations",
            json={"mode": mode, "title": f"Test {mode.capitalize()} Mode"},
            headers=auth_headers
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["mode"] == mode

        # Send a prompt specific to this mode
        msg_resp = client.post(
            f"/api/v1/mentor/conversations/{data['id']}/messages",
            json={"content": f"Advice on my strategy for {mode}?"},
            headers=auth_headers
        )
        assert msg_resp.status_code == 200
        assert msg_resp.json()["sender"] == "mentor"


def test_research_gap_analysis_grounding_and_limited_evidence(client: TestClient, auth_headers: dict):
    """Verifies gap analysis generation, epistemic limitation notices, grounded citations, and persistence."""
    proj_id, idea_id = create_test_project_and_idea(client, auth_headers)

    # 1. Generate with NO saved papers in project: should yield evidence_status == "limited"
    gap_resp = client.post(
        f"/api/v1/projects/{proj_id}/gaps/generate",
        json={"idea_id": idea_id},
        headers=auth_headers
    )
    assert gap_resp.status_code == 201
    gap_data = gap_resp.json()

    assert gap_data["evidence_status"] == "limited"
    assert gap_data["evidence_limitation_notice"] is not None
    assert "limited" in gap_data["evidence_limitation_notice"].lower() or "0" in gap_data["evidence_limitation_notice"]
    assert len(gap_data["identified_gaps"]) >= 2
    assert len(gap_data["suggested_research_questions"]) >= 2
    assert len(gap_data["proposed_evaluation_methods"]) >= 2

    # 2. Save 2 verified research papers in the project library
    paper1 = {
        "title": "Low-Power Convolutional Neural Networks on Microcontrollers",
        "authors": ["A. Author", "B. Scientist"],
        "abstract": "Energy-efficient edge inference using 4-bit INT quantization on ARM Cortex-M4.",
        "publication_date": "2023-05-15",
        "doi": "10.1145/3576841.12345",
        "source": "openalex",
        "original_url": "https://doi.org/10.1145/3576841.12345"
    }
    paper2 = {
        "title": "Empirical Limitations of Flash Memory in TinyML Anomaly Detection",
        "authors": ["C. Engineer", "D. Researcher"],
        "abstract": "Flash endurance degradation under continuous sensory write cycles in remote IoT deployments.",
        "publication_date": "2024-01-20",
        "doi": "10.1109/TMC.2024.98765",
        "source": "crossref",
        "original_url": "https://doi.org/10.1109/TMC.2024.98765"
    }
    client.post(f"/api/v1/research/projects/{proj_id}/papers/save", json=paper1, headers=auth_headers)
    client.post(f"/api/v1/research/projects/{proj_id}/papers/save", json=paper2, headers=auth_headers)

    # 3. Re-generate gap analysis: should now ground evidence and transition status to moderate/rich
    gap_resp2 = client.post(
        f"/api/v1/projects/{proj_id}/gaps/generate",
        json={"idea_id": idea_id},
        headers=auth_headers
    )
    assert gap_resp2.status_code == 201
    gap_data2 = gap_resp2.json()

    assert gap_data2["evidence_status"] in ["moderate", "rich"]
    assert len(gap_data2["citations"]) >= 2
    # Check that citations include the real papers saved with their URLs
    citation_urls = [c.get("source_url") for c in gap_data2["citations"]]
    assert any("doi.org" in str(url) for url in citation_urls)

    # 4. Verify retrieval via GET /projects/{project_id}/gaps
    list_resp = client.get(f"/api/v1/projects/{proj_id}/gaps", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_gap_analysis_tenant_isolation(client: TestClient, auth_headers: dict, second_user_headers: dict):
    """Ensures a user cannot view or generate gap analyses for another user's project."""
    proj_id, idea_id = create_test_project_and_idea(client, auth_headers)

    # User 2 attempts to generate gap analysis on User 1's project
    gen_resp = client.post(
        f"/api/v1/projects/{proj_id}/gaps/generate",
        json={"idea_id": idea_id},
        headers=second_user_headers
    )
    assert gen_resp.status_code in [403, 404]

    # User 2 attempts to retrieve gap analyses from User 1's project
    get_resp = client.get(f"/api/v1/projects/{proj_id}/gaps", headers=second_user_headers)
    assert get_resp.status_code in [403, 404]


def test_roadmap_generation_persistence_and_task_editing(client: TestClient, auth_headers: dict):
    """Verifies roadmap generation, architecture breakdown, task status toggle, task detail edits, and persistence."""
    proj_id, idea_id = create_test_project_and_idea(client, auth_headers)

    # 1. Generate roadmap
    gen_resp = client.post(
        f"/api/v1/projects/{proj_id}/roadmap/generate",
        json={"idea_id": idea_id},
        headers=auth_headers
    )
    assert gen_resp.status_code == 201
    roadmap = gen_resp.json()

    assert len(roadmap["objectives"]) >= 2
    assert len(roadmap["mvp_scope"]) >= 2
    assert len(roadmap["phased_milestones"]) >= 3
    assert len(roadmap["task_breakdown"]) >= 4
    assert len(roadmap["effort_estimate_assumptions"]) >= 2
    assert len(roadmap["risks_and_mitigations"]) >= 2

    # Check task fields
    task_0 = roadmap["task_breakdown"][0]
    task_id = task_0["id"]
    assert "priority" in task_0
    assert "status" in task_0
    assert "estimated_days" in task_0

    # 2. Toggle task status to in_progress
    status_resp = client.put(
        f"/api/v1/projects/{proj_id}/roadmap/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=auth_headers
    )
    assert status_resp.status_code == 200
    updated_roadmap = status_resp.json()
    updated_task = next(t for t in updated_roadmap["task_breakdown"] if t["id"] == task_id)
    assert updated_task["status"] == "in_progress"

    # 3. Edit task details (title, priority, estimated_days, status)
    edit_resp = client.put(
        f"/api/v1/projects/{proj_id}/roadmap/tasks/{task_id}",
        json={"status": "done", "priority": "high", "title": "Refined INT4 Quantization Kernel", "estimated_days": 8},
        headers=auth_headers
    )
    assert edit_resp.status_code == 200
    edited_roadmap = edit_resp.json()
    edited_task = next(t for t in edited_roadmap["task_breakdown"] if t["id"] == task_id)
    assert edited_task["status"] == "done"
    assert edited_task["priority"] == "high"
    assert edited_task["title"] == "Refined INT4 Quantization Kernel"
    assert edited_task["estimated_days"] == 8

    # 4. Verify persistence via GET /projects/{project_id}/roadmap
    get_resp = client.get(f"/api/v1/projects/{proj_id}/roadmap", headers=auth_headers)
    assert get_resp.status_code == 200
    persisted_roadmaps = get_resp.json()
    assert len(persisted_roadmaps) >= 1
    persisted_task = next(t for t in persisted_roadmaps[0]["task_breakdown"] if t["id"] == task_id)
    assert persisted_task["status"] == "done"
    assert persisted_task["priority"] == "high"
    assert persisted_task["title"] == "Refined INT4 Quantization Kernel"


def test_roadmap_tenant_isolation(client: TestClient, auth_headers: dict, second_user_headers: dict):
    """Ensures a user cannot view, generate, or modify another user's implementation roadmap."""
    proj_id, idea_id = create_test_project_and_idea(client, auth_headers)

    gen_resp = client.post(
        f"/api/v1/projects/{proj_id}/roadmap/generate",
        json={"idea_id": idea_id},
        headers=auth_headers
    )
    assert gen_resp.status_code == 201
    task_id = gen_resp.json()["task_breakdown"][0]["id"]

    # User 2 attempts to generate roadmap on User 1's project
    assert client.post(
        f"/api/v1/projects/{proj_id}/roadmap/generate",
        json={"idea_id": idea_id},
        headers=second_user_headers
    ).status_code in [403, 404]

    # User 2 attempts to retrieve roadmap from User 1's project
    assert client.get(
        f"/api/v1/projects/{proj_id}/roadmap",
        headers=second_user_headers
    ).status_code in [403, 404]

    # User 2 attempts to edit task in User 1's roadmap
    assert client.put(
        f"/api/v1/projects/{proj_id}/roadmap/tasks/{task_id}",
        json={"status": "done"},
        headers=second_user_headers
    ).status_code in [403, 404]
