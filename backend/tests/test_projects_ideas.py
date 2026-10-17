def test_project_crud_and_user_isolation(client, auth_headers, second_user_headers):
    # 1. User 1 creates project
    create_res = client.post("/api/v1/projects/", headers=auth_headers, json={
        "title": "Quantum Error Correction Accelerator",
        "description": "Hardware and compiler innovation for fault-tolerant qubits",
        "domain": "Quantum Computing"
    })
    assert create_res.status_code == 201
    proj_id = create_res.json()["id"]

    # 2. User 1 can access it
    get_res = client.get(f"/api/v1/projects/{proj_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Quantum Error Correction Accelerator"

    # 3. User 2 tries to access User 1's project -> MUST BE REJECTED (403 Forbidden)
    unauthorized_res = client.get(f"/api/v1/projects/{proj_id}", headers=second_user_headers)
    assert unauthorized_res.status_code == 403

    # 4. User 2 tries to delete User 1's project -> MUST BE REJECTED (403 Forbidden)
    unauthorized_del = client.delete(f"/api/v1/projects/{proj_id}", headers=second_user_headers)
    assert unauthorized_del.status_code == 403


def test_idea_submission_and_three_idea_limit(client, auth_headers):
    # Create project
    proj_res = client.post("/api/v1/projects/", headers=auth_headers, json={
        "title": "Healthcare Diagnostic Platform",
        "domain": "Biotech"
    })
    proj_id = proj_res.json()["id"]

    idea_base = {
        "problem_statement": "Diagnostic delays cause progressive patient deterioration in emergency triage.",
        "proposed_solution": "Edge-computed spectral imaging integrated with rapid biomarker scoring.",
        "target_audience": "Emergency room physicians and triage technicians",
        "industry": "Healthcare",
        "intended_use_case": "Rapid bedside assessment within 90 seconds of arrival",
        "expected_benefits": "Reduction of triage backlog by 60% with higher clinical accuracy."
    }

    # Submit Idea 1
    res1 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        **idea_base,
        "title": "Idea Alpha: Spectral Edge Triage"
    })
    assert res1.status_code == 201
    assert res1.json()["is_selected"] is True  # First idea is selected by default

    # Submit Idea 2
    res2 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        **idea_base,
        "title": "Idea Beta: Microfluidic Blood Strip Reader"
    })
    assert res2.status_code == 201

    # Submit Idea 3
    res3 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        **idea_base,
        "title": "Idea Gamma: Acoustic Pulmonary Sensor"
    })
    assert res3.status_code == 201

    # Attempt to submit Idea 4 -> MUST BE REJECTED (Max 3 ideas per project)
    res4 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        **idea_base,
        "title": "Idea Delta: Excessive Candidate"
    })
    assert res4.status_code == 400
    assert "at most 3 ideas" in res4.json()["detail"]


def test_select_idea(client, auth_headers):
    # Create project and 2 ideas
    proj_res = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Selection Test"})
    proj_id = proj_res.json()["id"]

    idea_payload = {
        "problem_statement": "Problem description with sufficient detail.",
        "proposed_solution": "Proposed solution with adequate engineering scope.",
        "target_audience": "Developers",
        "industry": "Developer Tools",
        "intended_use_case": "Continuous Integration",
        "expected_benefits": "Faster releases"
    }

    i1 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={**idea_payload, "title": "First"}).json()
    i2 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={**idea_payload, "title": "Second"}).json()

    assert i1["is_selected"] is True
    assert i2["is_selected"] is False

    # Select idea 2
    select_res = client.post(f"/api/v1/ideas/{i2['id']}/select", headers=auth_headers)
    assert select_res.status_code == 200
    assert select_res.json()["is_selected"] is True

    # Verify idea 1 is now unselected
    list_res = client.get(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers)
    ideas = list_res.json()
    assert [i for i in ideas if i["id"] == i1["id"]][0]["is_selected"] is False
    assert [i for i in ideas if i["id"] == i2["id"]][0]["is_selected"] is True
