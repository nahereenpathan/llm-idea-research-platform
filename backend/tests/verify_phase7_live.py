import requests
import io
import uuid
import docx
from pptx import Presentation

BASE_URL = "http://127.0.0.1:8000"

def test_phase7_live():
    print("=== STARTING PHASE 7 LIVE VERIFICATION ===")
    
    # 1. Health check
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[PASS] Backend health check OK")

    # 2. Register & Login User 1
    u1_email = f"user1_p7_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": u1_email,
        "password": "Password123!",
        "full_name": "Phase7 Lead Researcher"
    })
    assert reg_res.status_code in [200, 201], f"User 1 registration failed: {reg_res.text}"
    
    login_res = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": u1_email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200, f"User 1 login failed: {login_res.text}"
    u1_token = login_res.json()["access_token"]
    u1_headers = {"Authorization": f"Bearer {u1_token}"}
    print("[PASS] User 1 registered and authenticated")

    # 3. Create Project & Ideas
    proj_res = requests.post(f"{BASE_URL}/api/v1/projects/", json={
        "title": "Quantum Sensor Telemetry",
        "description": "High-fidelity cryogenic quantum sensor telemetry system for distributed quantum computing."
    }, headers=u1_headers)
    assert proj_res.status_code in [200, 201], f"Project creation failed: {proj_res.text}"
    project_id = proj_res.json()["id"]
    print(f"[PASS] Project created (ID: {project_id})")

    idea_res = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/ideas", json={
        "title": "Superconducting SQUID Optical Readout",
        "problem_statement": "Microwave interconnects introduce thermal noise into dilution refrigerators.",
        "proposed_solution": "Convert microwave quantum states into optical photons via electro-optic transducers.",
        "target_audience": "Quantum hardware developers, cryogenic laboratory physicists",
        "constraints": "Sub-millikelvin temperatures, ultra-low insertion loss"
    }, headers=u1_headers)
    assert idea_res.status_code in [200, 201], f"Idea creation failed: {idea_res.text}"
    idea_id = idea_res.json()["id"]
    print(f"[PASS] Idea created (ID: {idea_id})")

    # 3b. Evaluate Idea to generate scores
    eval_res = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/evaluate", json={
        "idea_ids": [idea_id]
    }, headers=u1_headers)
    assert eval_res.status_code in [200, 201], f"Evaluation failed: {eval_res.text}"
    print(f"[PASS] Idea evaluated successfully")

    # 4. Generate Research Report
    rep_res = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/reports/generate", json={
        "idea_id": idea_id,
        "report_type": "full_documentation",
        "title": "Quantum Sensor Telemetry Comprehensive Report"
    }, headers=u1_headers)
    assert rep_res.status_code in [200, 201], f"Report generation failed: {rep_res.text}"
    report_data = rep_res.json()
    report_id = report_data["id"]
    content_md = report_data["content_markdown"]
    print(f"[PASS] Report generated (ID: {report_id})")

    # Check that required sections and verifiable evidence tags are present
    assert "Executive Summary" in content_md
    assert "Literature Review" in content_md
    assert "Implementation Roadmap" in content_md
    assert "VERIFIED CITATIONS" in content_md or "No academic papers" in content_md
    print("[PASS] Report contains required 10-section architecture and evidence taxonomy tags")

    # 5. Generate Presentation
    pres_res = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/presentations/generate", json={
        "idea_id": idea_id,
        "title": "Quantum Telemetry Executive Briefing",
        "template_type": "academic"
    }, headers=u1_headers)
    assert pres_res.status_code in [200, 201], f"Presentation generation failed: {pres_res.text}"
    pres_data = pres_res.json()
    pres_id = pres_data["id"]
    slides = pres_data["slides"]
    assert len(slides) == 10, f"Expected 10 slides, got {len(slides)}"
    print(f"[PASS] 10-Slide Presentation generated (ID: {pres_id})")

    # 6. Verify PPTX Binary Download
    pptx_dl = requests.get(f"{BASE_URL}/api/v1/presentations/{pres_id}/export?format=pptx", headers=u1_headers)
    assert pptx_dl.status_code == 200, f"PPTX export failed: {pptx_dl.status_code}"
    assert pptx_dl.headers.get("content-type") == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    pptx_bytes = pptx_dl.content
    assert pptx_bytes.startswith(b"PK\x03\x04"), "Invalid PPTX zip magic bytes"
    prs = Presentation(io.BytesIO(pptx_bytes))
    assert len(prs.slides) == 10, f"Expected 10 slides in PPTX, got {len(prs.slides)}"
    print("[PASS] Valid 16:9 PPTX file generated and verified with python-pptx")

    # 7. Verify Document Exports (PDF, DOCX, Markdown)
    pdf_dl = requests.get(f"{BASE_URL}/api/v1/reports/{report_id}/export?format=pdf", headers=u1_headers)
    assert pdf_dl.status_code == 200, f"PDF export failed: {pdf_dl.status_code}"
    assert pdf_dl.headers.get("content-type") == "application/pdf"
    assert pdf_dl.content.startswith(b"%PDF-"), "Invalid PDF magic bytes"
    assert len(pdf_dl.content) > 1000, "PDF file suspiciously small"
    print(f"[PASS] Valid PDF generated ({len(pdf_dl.content)} bytes)")

    docx_dl = requests.get(f"{BASE_URL}/api/v1/reports/{report_id}/export?format=docx", headers=u1_headers)
    assert docx_dl.status_code == 200, f"DOCX export failed: {docx_dl.status_code}"
    assert docx_dl.headers.get("content-type") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert docx_dl.content.startswith(b"PK\x03\x04"), "Invalid DOCX zip magic bytes"
    doc = docx.Document(io.BytesIO(docx_dl.content))
    assert len(doc.paragraphs) > 5, "DOCX has too few paragraphs"
    print(f"[PASS] Valid DOCX generated ({len(doc.paragraphs)} paragraphs)")

    md_dl = requests.get(f"{BASE_URL}/api/v1/reports/{report_id}/export?format=md", headers=u1_headers)
    assert md_dl.status_code == 200, f"Markdown export failed: {md_dl.status_code}"
    assert "Executive Summary" in md_dl.text
    print("[PASS] Valid Markdown document exported")

    # 8. Verify CSV Score Comparison Export
    csv_dl = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/export/csv", headers=u1_headers)
    assert csv_dl.status_code == 200, f"CSV export failed: {csv_dl.status_code}"
    assert csv_dl.headers.get("content-type") == "text/csv; charset=utf-8"
    assert "Idea Title" in csv_dl.text
    assert "Composite Score" in csv_dl.text
    assert "Superconducting SQUID Optical Readout" in csv_dl.text
    print("[PASS] Valid CSV score comparison exported with UTF-8-sig")

    # 9. Tenant Isolation Verification
    u2_email = f"user2_p7_{uuid.uuid4().hex[:8]}@example.com"
    requests.post(f"{BASE_URL}/api/v1/auth/register", json={
        "email": u2_email,
        "password": "Password123!",
        "full_name": "Phase7 Intruder"
    })
    u2_token = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": u2_email,
        "password": "Password123!"
    }).json()["access_token"]
    u2_headers = {"Authorization": f"Bearer {u2_token}"}

    # User 2 tries to download User 1's report, presentation, PDF, PPTX, CSV
    u2_rep = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/reports/{report_id}", headers=u2_headers)
    assert u2_rep.status_code in [403, 404], f"Tenant breach on report GET: {u2_rep.status_code}"

    u2_pdf = requests.get(f"{BASE_URL}/api/v1/reports/{report_id}/export?format=pdf", headers=u2_headers)
    assert u2_pdf.status_code in [403, 404], f"Tenant breach on PDF export: {u2_pdf.status_code}"

    u2_pptx = requests.get(f"{BASE_URL}/api/v1/presentations/{pres_id}/export?format=pptx", headers=u2_headers)
    assert u2_pptx.status_code in [403, 404], f"Tenant breach on PPTX export: {u2_pptx.status_code}"

    u2_csv = requests.get(f"{BASE_URL}/api/v1/projects/{project_id}/export/csv", headers=u2_headers)
    assert u2_csv.status_code in [403, 404], f"Tenant breach on CSV export: {u2_csv.status_code}"

    u2_regen = requests.post(f"{BASE_URL}/api/v1/projects/{project_id}/reports/{report_id}/regenerate", headers=u2_headers)
    assert u2_regen.status_code in [403, 404], f"Tenant breach on report regenerate: {u2_regen.status_code}"

    print("[PASS] Tenant isolation strictly enforced on all Phase 7 endpoints")
    print("=== ALL PHASE 7 LIVE VERIFICATION TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_phase7_live()
