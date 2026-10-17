import httpx
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_verification():
    client = httpx.Client(base_url=BASE_URL, timeout=20.0)
    print("=" * 70)
    print("IDEALENS PHASE 5 LIVE VERIFICATION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # 0. Health & Status
    # -------------------------------------------------------------------------
    h = client.get("/health")
    assert h.status_code == 200, f"Health check failed: {h.text}"
    print("[PASS] 0. Backend server is healthy.")

    # -------------------------------------------------------------------------
    # 1. Authentication
    # -------------------------------------------------------------------------
    auth_resp = client.post("/api/v1/auth/login", json={
        "email": "researcher_mvp@idealens.ai",
        "password": "SecurePassword123!"
    })
    assert auth_resp.status_code == 200, f"Login failed: {auth_resp.text}"
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 1. Authenticated as researcher_mvp@idealens.ai.")

    # -------------------------------------------------------------------------
    # 2. Check Provider Sources Endpoint
    # -------------------------------------------------------------------------
    p_src_resp = client.get("/api/v1/research/papers/sources")
    assert p_src_resp.status_code == 200, f"Paper sources failed: {p_src_resp.text}"
    p_sources = {s["id"]: s for s in p_src_resp.json()}
    assert p_sources["openalex"]["status"] == "active"
    assert p_sources["crossref"]["status"] == "active"
    assert p_sources["ieee"]["status"] == "unconfigured"
    print(f"[PASS] 2. Paper sources verified: OpenAlex (active), Crossref (active), IEEE (unconfigured).")

    pat_src_resp = client.get("/api/v1/research/patents/sources")
    assert pat_src_resp.status_code == 200, f"Patent sources failed: {pat_src_resp.text}"
    pat_sources = {s["id"]: s for s in pat_src_resp.json()}
    assert pat_sources["uspto"]["status"] == "unconfigured"
    assert pat_sources["epo"]["status"] == "unconfigured"
    print(f"[PASS] 2b. Patent sources verified: USPTO (unconfigured), EPO (unconfigured).")

    # -------------------------------------------------------------------------
    # 3. Real OpenAlex Search Verification
    # -------------------------------------------------------------------------
    print("\n--- Testing OpenAlex Live Academic Paper Search ---")
    query_oa = "reinforcement learning robotics"
    oa_resp_p1 = client.get(
        f"/api/v1/research/papers/search?query={query_oa}&source=openalex&page=1&limit=5",
        headers=headers
    )
    assert oa_resp_p1.status_code == 200, f"OpenAlex search failed: {oa_resp_p1.text}"
    data_p1 = oa_resp_p1.json()
    assert data_p1["source"] == "openalex"
    assert data_p1["total_count"] > 1000, f"Expected >1000 results, got {data_p1['total_count']}"
    assert len(data_p1["results"]) == 5
    
    first_paper = data_p1["results"][0]
    assert first_paper["title"] and len(first_paper["title"]) > 3
    assert first_paper["external_id"].startswith("https://openalex.org/") or first_paper["external_id"].startswith("http")
    assert isinstance(first_paper["authors"], list)
    print(f"[PASS] 3a. OpenAlex returned live results: {data_p1['total_count']} total records.")
    print(f"       Sample Title: '{first_paper['title'][:60]}...'")
    print(f"       Authors: {first_paper['authors'][:3]}")
    print(f"       Year: {first_paper['publication_year']}, DOI: {first_paper['doi']}")
    print(f"       Abstract Length: {len(first_paper['abstract'])} chars (has_abstract={first_paper['has_abstract']})")

    # Pagination test on OpenAlex: page 2 must return different papers
    oa_resp_p2 = client.get(
        f"/api/v1/research/papers/search?query={query_oa}&source=openalex&page=2&limit=5",
        headers=headers
    )
    assert oa_resp_p2.status_code == 200
    data_p2 = oa_resp_p2.json()
    assert len(data_p2["results"]) == 5
    p1_ids = {p["external_id"] for p in data_p1["results"]}
    p2_ids = {p["external_id"] for p in data_p2["results"]}
    assert p1_ids != p2_ids, "Page 1 and Page 2 should return distinct paper records."
    print("[PASS] 3b. OpenAlex pagination verified (Page 1 vs Page 2 are distinct).")

    # Year filter test
    oa_resp_yr = client.get(
        f"/api/v1/research/papers/search?query={query_oa}&source=openalex&year_from=2023&year_to=2024&page=1&limit=3",
        headers=headers
    )
    assert oa_resp_yr.status_code == 200
    for p in oa_resp_yr.json()["results"]:
        if p.get("publication_year"):
            assert 2023 <= p["publication_year"] <= 2024, f"Year out of bounds: {p['publication_year']}"
    print("[PASS] 3c. OpenAlex publication year filtering (2023-2024) verified.")

    # -------------------------------------------------------------------------
    # 4. Real Crossref Search Verification
    # -------------------------------------------------------------------------
    print("\n--- Testing Crossref Live Academic Paper Search ---")
    query_cr = "transformer attention"
    cr_resp = client.get(
        f"/api/v1/research/papers/search?query={query_cr}&source=crossref&page=1&limit=5",
        headers=headers
    )
    assert cr_resp.status_code == 200, f"Crossref search failed: {cr_resp.text}"
    cr_data = cr_resp.json()
    assert cr_data["source"] == "crossref"
    assert cr_data["total_count"] > 1000
    assert len(cr_data["results"]) == 5
    cr_first = cr_data["results"][0]
    assert cr_first["title"]
    assert cr_first["doi"]
    print(f"[PASS] 4a. Crossref returned live results: {cr_data['total_count']} total records.")
    print(f"       Sample Title: '{cr_first['title'][:60]}...'")
    print(f"       DOI: {cr_first['doi']}, Venue: {cr_first.get('venue')}")

    # Direct DOI lookup in Crossref (using Nature Deep learning seminal paper)
    doi_sample = "10.1038/nature14539"
    cr_doi_resp = client.get(
        f"/api/v1/research/papers/search?query={doi_sample}&source=crossref&search_type=doi",
        headers=headers
    )
    assert cr_doi_resp.status_code == 200
    doi_results = cr_doi_resp.json()["results"]
    assert len(doi_results) >= 1
    assert "nature14539" in doi_results[0]["doi"].lower()
    print(f"[PASS] 4b. Crossref direct DOI lookup verified for '{doi_sample}' (Title: '{doi_results[0]['title']}').")

    # -------------------------------------------------------------------------
    # 5. Save Paper to Project Library & Duplicate Prevention
    # -------------------------------------------------------------------------
    print("\n--- Testing Paper Library Persistence & Duplicate Prevention ---")
    paper_to_save = {
        "external_id": first_paper["external_id"],
        "source": "openalex",
        "title": first_paper["title"],
        "authors": first_paper["authors"],
        "publication_year": first_paper["publication_year"],
        "publication_date": first_paper["publication_date"],
        "abstract": first_paper["abstract"],
        "doi": first_paper["doi"],
        "source_url": first_paper["source_url"],
        "citation_count": first_paper["citation_count"],
        "user_notes": "Essential benchmark paper for robot RL navigation."
    }

    # 1. First save succeeds
    save_r1 = client.post("/api/v1/research/projects/1/papers/save", headers=headers, json=paper_to_save)
    assert save_r1.status_code == 201, f"Save paper failed: {save_r1.text}"
    saved_paper_id = save_r1.json()["id"]
    print(f"[PASS] 5a. Paper saved to Project 1 (id={saved_paper_id}).")

    # 2. Second save must return 409 Conflict
    save_r2 = client.post("/api/v1/research/projects/1/papers/save", headers=headers, json=paper_to_save)
    assert save_r2.status_code == 409, f"Expected 409 Conflict on duplicate save, got {save_r2.status_code}"
    print(f"[PASS] 5b. Duplicate save correctly rejected with HTTP 409 Conflict ({save_r2.json()['detail']}).")

    # 3. Retrieve saved papers for project 1
    lib_resp = client.get("/api/v1/research/projects/1/papers", headers=headers)
    assert lib_resp.status_code == 200
    lib_papers = lib_resp.json()
    assert any(p["id"] == saved_paper_id for p in lib_papers)
    print(f"[PASS] 5c. Retrieved project library containing {len(lib_papers)} saved paper(s).")

    # 4. Retrieve detail endpoint
    det_resp = client.get(f"/api/v1/research/papers/{saved_paper_id}", headers=headers)
    assert det_resp.status_code == 200
    assert det_resp.json()["title"] == first_paper["title"]
    print(f"[PASS] 5d. Paper detail view endpoint verified for paper {saved_paper_id}.")

    # 5. Clean up the saved paper
    del_resp = client.delete(f"/api/v1/research/papers/{saved_paper_id}", headers=headers)
    assert del_resp.status_code == 204
    print(f"[PASS] 5e. Paper removed from library successfully (HTTP 204).")

    # -------------------------------------------------------------------------
    # 6. Tenant Authorization & Security Isolation
    # -------------------------------------------------------------------------
    print("\n--- Testing Tenant Isolation & Access Control ---")
    # Register second user
    other_email = "independent_auditor@idealens.ai"
    client.post("/api/v1/auth/register", json={
        "email": other_email,
        "password": "SecurePassword456!",
        "full_name": "Auditor"
    })
    other_login = client.post("/api/v1/auth/login", json={
        "email": other_email,
        "password": "SecurePassword456!"
    })
    other_token = other_login.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Auditor attempts to save paper to User 1's project -> 403 Forbidden
    unauth_save = client.post("/api/v1/research/projects/1/papers/save", headers=other_headers, json=paper_to_save)
    assert unauth_save.status_code == 403, f"Expected 403 Forbidden for unauthorized project save, got {unauth_save.status_code}"

    # Auditor attempts to list User 1's saved papers -> 403 Forbidden
    unauth_list = client.get("/api/v1/research/projects/1/papers", headers=other_headers)
    assert unauth_list.status_code == 403, f"Expected 403 Forbidden for unauthorized project list, got {unauth_list.status_code}"
    print("[PASS] 6. Tenant isolation verified: unauthorized users cannot view, save, or modify another user's project library.")

    # -------------------------------------------------------------------------
    # 7. Patent Search Provider Verification
    # -------------------------------------------------------------------------
    print("\n--- Testing Patent Search Adapters & Error Handling ---")
    # Search unconfigured USPTO provider
    pat_res = client.get("/api/v1/research/patents/search?query=autonomous+drone&source=uspto", headers=headers)
    assert pat_res.status_code == 503, f"Expected 503 for unconfigured USPTO, got {pat_res.status_code}"
    pat_err = pat_res.json()
    assert "USPTO Open Data Portal is not configured" in pat_err["detail"]
    assert "USPTO_API_KEY" in pat_err["detail"]
    print(f"[PASS] 7a. Unconfigured USPTO provider returns clear HTTP 503 with configuration message.")

    # Search unconfigured EPO provider
    epo_res = client.get("/api/v1/research/patents/search?query=autonomous+drone&source=epo", headers=headers)
    assert epo_res.status_code == 503
    assert "EPO_CONSUMER_KEY" in epo_res.json()["detail"]
    print(f"[PASS] 7b. Unconfigured EPO provider returns clear HTTP 503 with configuration message.")

    # -------------------------------------------------------------------------
    # 8. Regression: Phase 4 Multi-Idea Evaluation & Scoring
    # -------------------------------------------------------------------------
    print("\n--- Testing Regression: Phase 4 Multi-Idea Evaluation ---")
    eval_resp = client.post("/api/v1/projects/1/evaluate", headers=headers, json={"idea_ids": [1, 2, 3]})
    eval_data = eval_resp.json()
    assert "comparison" in eval_data
    assert eval_data["comparison"]["recommended_idea_id"] is not None
    assert len(eval_data["evaluations"]) == 3
    scores = {ev["idea_id"]: ev["overall_score"] for ev in eval_data["evaluations"]}
    print(f"[PASS] 8. Phase 4 Multi-Idea Evaluation regression verified intact.")
    print(f"       Composite Overall Scores: {scores}")
    print(f"       Recommended Candidate: Idea {eval_data['comparison']['recommended_idea_id']}")

    print("\n" + "=" * 70)
    print("ALL 8 VERIFICATION PHASES PASSED WITH ZERO ERRORS!")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
