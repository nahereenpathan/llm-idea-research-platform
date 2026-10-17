import io
import csv
import pytest
from pptx import Presentation as PPTXDoc
from docx import Document as DocxDoc
from fastapi.testclient import TestClient


def create_test_project_and_idea_with_evidence(client: TestClient, headers: dict):
    """Helper to establish a rich test project with an idea, saved papers, patents, evaluation, gap analysis, and roadmap."""
    # 1. Project
    proj_resp = client.post(
        "/api/v1/projects/",
        json={"title": "Autonomous Drone Fleet Network", "description": "Swarm robotics for search & rescue"},
        headers=headers
    )
    assert proj_resp.status_code == 201
    proj_id = proj_resp.json()["id"]

    # 2. Idea
    idea_resp = client.post(
        f"/api/v1/projects/{proj_id}/ideas",
        json={
            "title": "Mesh Protocol Decentralized Relay",
            "problem_statement": "Cellular infrastructure fails during seismic disasters, preventing real-time coordination.",
            "target_audience": "Search and Rescue disaster responders and municipal emergency personnel.",
            "proposed_solution": "Deploy 802.11ah Sub-GHz HaLow ad-hoc mesh topology with self-healing dynamic routing.",
            "industry": "Robotics & Telecommunications",
            "intended_use_case": "Disaster response mesh communications",
            "expected_benefits": "Zero dependency on cellular towers and 10x range extension."
        },
        headers=headers
    )
    assert idea_resp.status_code == 201
    idea_id = idea_resp.json()["id"]

    # 3. Save 2 Academic Papers
    paper1 = {
        "title": "Sub-GHz Wireless Mesh Networks in Disaster Scenarios",
        "authors": ["E. Davis", "F. Miller"],
        "abstract": "Empirical evaluation of 802.11ah throughput and packet delivery ratio in collapsed urban environments.",
        "publication_date": "2023-04-12",
        "doi": "10.1109/SURV.2023.10001",
        "source": "openalex",
        "original_url": "https://doi.org/10.1109/SURV.2023.10001"
    }
    paper2 = {
        "title": "Decentralized Routing Protocols for UAV Swarms",
        "authors": ["G. Zhang", "H. Kumar"],
        "abstract": "Dynamic link recovery and latency trade-offs under high mobility aerial mesh topologies.",
        "publication_date": "2024-02-18",
        "doi": "10.1016/j.adhoc.2024.10300",
        "source": "crossref",
        "original_url": "https://doi.org/10.1016/j.adhoc.2024.10300"
    }
    client.post(f"/api/v1/research/projects/{proj_id}/papers/save", json=paper1, headers=headers)
    client.post(f"/api/v1/research/projects/{proj_id}/papers/save", json=paper2, headers=headers)

    # 4. Save 1 Patent
    patent1 = {
        "patent_number": "US-11582800-B2",
        "title": "Ad-hoc aerial mesh communication routing for search and rescue unmanned vehicles",
        "inventors": ["Alice Inventor", "Bob Engineer"],
        "publication_date": "2023-02-14",
        "abstract": "Methods for establishing dynamic wireless relay routes among autonomous airborne nodes.",
        "source": "uspto",
        "original_url": "https://patents.google.com/patent/US11582800B2/en"
    }
    client.post(f"/api/v1/research/projects/{proj_id}/patents/save", json=patent1, headers=headers)

    # 5. Run Evaluation
    eval_resp = client.post(
        f"/api/v1/projects/{proj_id}/evaluate",
        json={"idea_ids": [idea_id]},
        headers=headers
    )
    assert eval_resp.status_code == 200

    # 6. Generate Gap Analysis
    gap_resp = client.post(
        f"/api/v1/projects/{proj_id}/gaps/generate",
        json={"idea_id": idea_id},
        headers=headers
    )
    assert gap_resp.status_code == 201

    # 7. Generate Roadmap
    roadmap_resp = client.post(
        f"/api/v1/projects/{proj_id}/roadmap/generate",
        json={"idea_id": idea_id},
        headers=headers
    )
    assert roadmap_resp.status_code == 201

    return proj_id, idea_id


def test_research_report_generation_with_complete_evidence(client: TestClient, auth_headers: dict):
    """Verifies that the generated research report synthesizes all 10 sections grounded in DB evidence."""
    proj_id, idea_id = create_test_project_and_idea_with_evidence(client, auth_headers)

    # Generate full report
    rep_resp = client.post(
        f"/api/v1/projects/{proj_id}/reports/generate",
        json={"idea_id": idea_id, "report_type": "full_documentation"},
        headers=auth_headers
    )
    assert rep_resp.status_code == 201
    report = rep_resp.json()
    report_id = report["id"]

    assert report["report_type"] == "full_documentation"
    assert report["project_id"] == proj_id
    assert report["idea_id"] == idea_id

    md = report["content_markdown"]
    # Check that all core sections exist
    assert "## 1. Executive Summary" in md
    assert "## 2. Idea Evaluation" in md
    assert "## 3. Academic Literature Review" in md
    assert "## 4. Patent Landscape" in md
    assert "## 5. Research Gaps" in md
    assert "## 6. Technical Feasibility" in md
    assert "## 7. Implementation Roadmap" in md
    assert "## 8. Security, Privacy" in md
    assert "## 9. Strategic Recommendations" in md
    assert "## 10. References" in md

    # Check evidence citations and grounding
    assert "Sub-GHz Wireless Mesh Networks" in md
    assert "10.1109/SURV.2023.10001" in md
    assert "US-11582800-B2" in md

    # Verify retrieval
    get_resp = client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == report_id

    # Verify editing
    edit_resp = client.put(
        f"/api/v1/reports/{report_id}",
        json={"title": "Updated Whitepaper Title", "content_markdown": md + "\n\n## Appendix: Benchmarking"},
        headers=auth_headers
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json()["title"] == "Updated Whitepaper Title"
    assert "Appendix: Benchmarking" in edit_resp.json()["content_markdown"]


def test_research_report_generation_with_incomplete_evidence(client: TestClient, auth_headers: dict):
    """Verifies that when evidence is absent/incomplete, clear limitation notices are rendered."""
    proj_resp = client.post(
        "/api/v1/projects/",
        json={"title": "Minimal Project", "description": "Empty project with no literature"},
        headers=auth_headers
    )
    proj_id = proj_resp.json()["id"]

    idea_resp = client.post(
        f"/api/v1/projects/{proj_id}/ideas",
        json={
            "title": "Bare Idea",
            "problem_statement": "Manual accounting spreadsheet reconciliation is tedious and error prone.",
            "target_audience": "Small business bookkeepers.",
            "proposed_solution": "Automated receipt parsing and bank feed rule matcher."
        },
        headers=auth_headers
    )
    idea_id = idea_resp.json()["id"]

    # Generate report without papers, patents, or evaluation
    rep_resp = client.post(
        f"/api/v1/projects/{proj_id}/reports/generate",
        json={"idea_id": idea_id, "report_type": "proposal"},
        headers=auth_headers
    )
    assert rep_resp.status_code == 201
    md = rep_resp.json()["content_markdown"]

    # Must contain limitation note
    assert "Notice on Evidence Density" in md or "No academic papers have been saved" in md
    assert "No patent records currently saved" in md


def test_presentation_generator_and_pptx_validity(client: TestClient, auth_headers: dict):
    """Verifies 10-slide deck generation and valid binary PPTX export."""
    proj_id, idea_id = create_test_project_and_idea_with_evidence(client, auth_headers)

    # 1. Generate presentation
    pres_resp = client.post(
        f"/api/v1/projects/{proj_id}/presentations/generate",
        json={"idea_id": idea_id, "theme": "navy_modern", "template_type": "hackathon"},
        headers=auth_headers
    )
    assert pres_resp.status_code == 201
    deck = pres_resp.json()
    pres_id = deck["id"]
    slides = deck["slides"]

    assert len(slides) == 10
    # Slide 1: Title
    assert slides[0]["layout"] == "title"
    # Slide 4: Evaluation & Scoring
    assert "Evaluation & Scoring" in slides[3]["title"]
    # Slide 5: Academic Literature
    assert "Academic Literature" in slides[4]["title"]
    # Slide 10: Conclusion & References
    assert "References" in slides[9]["title"]

    # 2. Export PPTX file
    export_resp = client.get(f"/api/v1/presentations/{pres_id}/export?format=pptx", headers=auth_headers)
    assert export_resp.status_code == 200
    assert "presentationml.presentation" in export_resp.headers["content-type"]
    assert "attachment" in export_resp.headers["content-disposition"]
    assert export_resp.headers["content-disposition"].endswith('.pptx"')

    # 3. Validate binary PPTX using python-pptx
    pptx_bytes = io.BytesIO(export_resp.content)
    parsed_prs = PPTXDoc(pptx_bytes)
    assert len(parsed_prs.slides) == 10
    # Verify slide dimensions are 16:9 widescreen
    assert parsed_prs.slide_width.inches == pytest.approx(13.333, 0.01)
    assert parsed_prs.slide_height.inches == pytest.approx(7.5, 0.01)


def test_document_exports_validity(client: TestClient, auth_headers: dict):
    """Verifies that PDF, DOCX, Markdown, LaTeX, and CSV formats produce valid, non-empty files."""
    proj_id, idea_id = create_test_project_and_idea_with_evidence(client, auth_headers)

    rep_resp = client.post(
        f"/api/v1/projects/{proj_id}/reports/generate",
        json={"idea_id": idea_id, "report_type": "full_documentation"},
        headers=auth_headers
    )
    report_id = rep_resp.json()["id"]

    # 1. Test PDF Export
    pdf_resp = client.get(f"/api/v1/reports/{report_id}/export?format=pdf", headers=auth_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
    assert len(pdf_resp.content) > 1000

    # 2. Test DOCX Export
    docx_resp = client.get(f"/api/v1/reports/{report_id}/export?format=docx", headers=auth_headers)
    assert docx_resp.status_code == 200
    assert "wordprocessingml.document" in docx_resp.headers["content-type"]
    assert len(docx_resp.content) > 1000
    # Validate with python-docx
    docx_file = DocxDoc(io.BytesIO(docx_resp.content))
    assert len(docx_file.paragraphs) > 5

    # 3. Test Markdown Export
    md_resp = client.get(f"/api/v1/reports/{report_id}/export?format=md", headers=auth_headers)
    assert md_resp.status_code == 200
    assert "text/markdown" in md_resp.headers["content-type"]
    assert md_resp.text.startswith("# ")
    assert "Executive Summary" in md_resp.text

    # 4. Test LaTeX Export
    latex_resp = client.get(f"/api/v1/reports/{report_id}/export?format=latex", headers=auth_headers)
    assert latex_resp.status_code == 200
    assert "latex" in latex_resp.headers["content-type"]
    assert "\\documentclass" in latex_resp.text

    # 5. Test CSV Evaluation Scores Export
    csv_resp = client.get(f"/api/v1/projects/{proj_id}/export/csv", headers=auth_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "attachment" in csv_resp.headers["content-disposition"]
    assert "scores.csv" in csv_resp.headers["content-disposition"]

    # Parse and verify CSV contents
    csv_text = csv_resp.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) >= 1
    row = rows[0]
    assert row["Project ID"] == str(proj_id)
    assert row["Idea Title"] == "Mesh Protocol Decentralized Relay"
    assert row["Composite Score"] != "N/A"
    assert float(row["Composite Score"]) > 0
    assert row["Grade"] in ["A", "B", "C", "D", "F"]
    assert row["Strategic Recommendation"] != ""


def test_phase7_tenant_isolation(client: TestClient, auth_headers: dict, second_user_headers: dict):
    """Ensures that User 2 cannot view, edit, delete, or download User 1's reports, presentations, or CSVs."""
    proj_id, idea_id = create_test_project_and_idea_with_evidence(client, auth_headers)

    # User 1 creates report & presentation
    rep_resp = client.post(
        f"/api/v1/projects/{proj_id}/reports/generate",
        json={"idea_id": idea_id, "report_type": "proposal"},
        headers=auth_headers
    )
    report_id = rep_resp.json()["id"]

    pres_resp = client.post(
        f"/api/v1/projects/{proj_id}/presentations/generate",
        json={"idea_id": idea_id},
        headers=auth_headers
    )
    pres_id = pres_resp.json()["id"]

    # User 2 attempts unauthorized actions on Report
    assert client.get(f"/api/v1/reports/{report_id}", headers=second_user_headers).status_code in [403, 404]
    assert client.put(f"/api/v1/reports/{report_id}", json={"title": "Hacked"}, headers=second_user_headers).status_code in [403, 404]
    assert client.delete(f"/api/v1/reports/{report_id}", headers=second_user_headers).status_code in [403, 404]
    assert client.get(f"/api/v1/reports/{report_id}/export?format=pdf", headers=second_user_headers).status_code in [403, 404]
    assert client.get(f"/api/v1/reports/{report_id}/export?format=docx", headers=second_user_headers).status_code in [403, 404]

    # User 2 attempts unauthorized actions on Presentation
    assert client.get(f"/api/v1/presentations/{pres_id}", headers=second_user_headers).status_code in [403, 404]
    assert client.put(f"/api/v1/presentations/{pres_id}", json={"title": "Hacked"}, headers=second_user_headers).status_code in [403, 404]
    assert client.delete(f"/api/v1/presentations/{pres_id}", headers=second_user_headers).status_code in [403, 404]
    assert client.get(f"/api/v1/presentations/{pres_id}/export?format=pptx", headers=second_user_headers).status_code in [403, 404]

    # User 2 attempts unauthorized CSV export and export-all of User 1's project
    assert client.get(f"/api/v1/projects/{proj_id}/export/csv", headers=second_user_headers).status_code in [403, 404]
    assert client.get(f"/api/v1/projects/{proj_id}/export-all", headers=second_user_headers).status_code in [403, 404]
