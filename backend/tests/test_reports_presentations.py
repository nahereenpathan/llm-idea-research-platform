def test_report_lifecycle(client, auth_headers):
    # Create project and idea
    proj = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Report Test"}).json()
    proj_id = proj["id"]

    idea = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        "title": "Decentralized Energy Grid",
        "problem_statement": "Grid congestion causes rolling outages in microgrid clusters.",
        "proposed_solution": "Dynamic peer-to-peer auction settlement using cryptographic proofs.",
        "target_audience": "Municipal grid operators and residential solar producers",
        "industry": "CleanTech",
        "intended_use_case": "High-frequency local energy balance",
        "expected_benefits": "Zero blackouts and 25% lower energy transmission costs."
    }).json()

    # Generate Report
    rep_res = client.post(f"/api/v1/projects/{proj_id}/reports/generate", headers=auth_headers, json={
        "idea_id": idea["id"],
        "report_type": "feasibility"
    })
    assert rep_res.status_code == 201
    rep_data = rep_res.json()
    assert rep_data["report_type"] == "feasibility"
    assert len(rep_data["content_markdown"]) > 50
    rep_id = rep_data["id"]

    # Edit Report
    edit_res = client.put(f"/api/v1/reports/{rep_id}", headers=auth_headers, json={
        "title": "Customized CleanTech Feasibility Study",
        "content_markdown": "# Customized CleanTech Feasibility Study\n\nUpdated manual analysis notes."
    })
    assert edit_res.status_code == 200
    assert edit_res.json()["title"] == "Customized CleanTech Feasibility Study"


def test_presentation_lifecycle(client, auth_headers):
    # Create project
    proj = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Presentation Project"}).json()
    proj_id = proj["id"]

    # Generate 10-slide Presentation deck
    gen_res = client.post(f"/api/v1/projects/{proj_id}/presentations/generate", headers=auth_headers, json={
        "title": "Hackathon Pitch Deck",
        "theme": "navy_modern",
        "template_type": "hackathon"
    })
    assert gen_res.status_code == 201
    pres = gen_res.json()
    assert len(pres["slides"]) == 10
    pres_id = pres["id"]

    # Add a slide
    slide_res = client.post(f"/api/v1/presentations/{pres_id}/slides", headers=auth_headers, json={
        "slide_number": 11,
        "layout": "bullets",
        "title": "Bonus Appendix Slide",
        "content_json": {"bullets": ["Additional benchmark charts", "Security audit credentials"]}
    })
    assert slide_res.status_code == 201
    assert slide_res.json()["title"] == "Bonus Appendix Slide"

    # Update slide
    slide_id = slide_res.json()["id"]
    update_slide = client.put(f"/api/v1/slides/{slide_id}", headers=auth_headers, json={
        "title": "Updated Appendix Slide"
    })
    assert update_slide.status_code == 200
    assert update_slide.json()["title"] == "Updated Appendix Slide"

    # Delete slide
    del_slide = client.delete(f"/api/v1/slides/{slide_id}", headers=auth_headers)
    assert del_slide.status_code == 204


def test_ai_mentor_chat(client, auth_headers):
    # Create a mentoring session in technical mode
    conv_res = client.post("/api/v1/mentor/conversations", headers=auth_headers, json={
        "mode": "technical",
        "title": "Architecture Mentoring"
    })
    assert conv_res.status_code == 201
    conv = conv_res.json()
    assert conv["mode"] == "technical"
    assert len(conv["messages"]) >= 1  # Initial greeting

    conv_id = conv["id"]
    # Send a message
    msg_res = client.post(f"/api/v1/mentor/conversations/{conv_id}/messages", headers=auth_headers, json={
        "content": "What is the recommended caching pattern for high-read academic search results?"
    })
    assert msg_res.status_code == 200
    reply = msg_res.json()
    assert reply["sender"] == "mentor"
    assert len(reply["content"]) > 20
