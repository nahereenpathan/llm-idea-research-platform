def test_export_endpoints(client, auth_headers):
    # Create project, idea, and report
    proj = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Export Test Project"}).json()
    proj_id = proj["id"]

    idea = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        "title": "Autonomous Drone Fleet",
        "problem_statement": "Search and rescue operations in wilderness terrain suffer from high search latencies.",
        "proposed_solution": "Coordinated mesh-network drone swarms with onboard thermal vision.",
        "target_audience": "Search and rescue agencies",
        "industry": "Aerospace & Robotics",
        "intended_use_case": "Wilderness reconnaissance",
        "expected_benefits": "90% faster victim localization."
    }).json()

    rep = client.post(f"/api/v1/projects/{proj_id}/reports/generate", headers=auth_headers, json={
        "idea_id": idea["id"],
        "report_type": "proposal"
    }).json()
    rep_id = rep["id"]

    # 1. Test Markdown export
    md_res = client.get(f"/api/v1/reports/{rep_id}/export?format=md", headers=auth_headers)
    assert md_res.status_code == 200
    assert md_res.headers["content-type"].startswith("text/markdown")
    assert "attachment" in md_res.headers["content-disposition"]
    assert len(md_res.content) > 20

    # 2. Test LaTeX export
    tex_res = client.get(f"/api/v1/reports/{rep_id}/export?format=latex", headers=auth_headers)
    assert tex_res.status_code == 200
    assert "\\begin{document}" in tex_res.text

    # 3. Test DOCX export
    docx_res = client.get(f"/api/v1/reports/{rep_id}/export?format=docx", headers=auth_headers)
    assert docx_res.status_code == 200
    assert "wordprocessingml" in docx_res.headers["content-type"]
    assert len(docx_res.content) > 500

    # 4. Test PDF export
    pdf_res = client.get(f"/api/v1/reports/{rep_id}/export?format=pdf", headers=auth_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    # 5. Test Presentation PPTX export
    pres = client.post(f"/api/v1/projects/{proj_id}/presentations/generate", headers=auth_headers, json={
        "title": "Drone Pitch Deck",
        "theme": "navy_modern"
    }).json()
    pres_id = pres["id"]

    pptx_res = client.get(f"/api/v1/presentations/{pres_id}/export?format=pptx", headers=auth_headers)
    assert pptx_res.status_code == 200
    assert "presentationml" in pptx_res.headers["content-type"]
    assert len(pptx_res.content) > 1000

    # 6. Test Project full JSON bundle export
    all_res = client.get(f"/api/v1/projects/{proj_id}/export-all", headers=auth_headers)
    assert all_res.status_code == 200
    bundle = all_res.json()
    assert bundle["project"]["title"] == "Export Test Project"
    assert len(bundle["ideas"]) == 1
    assert len(bundle["reports"]) == 1
