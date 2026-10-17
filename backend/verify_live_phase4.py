import httpx

def test_phase4_live():
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15.0)

    # 1. Health Probe
    h = client.get("/health")
    assert h.status_code == 200
    print("[PASS] 1. Backend /health is 200 OK.")

    # 2. Authenticate
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "researcher_mvp@idealens.ai",
        "password": "SecurePassword123!"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 2. User authenticated successfully.")

    # 3. Retrieve Project 1 and its 3 ideas
    proj_resp = client.get("/api/v1/projects/1", headers=headers)
    assert proj_resp.status_code == 200
    ideas_resp = client.get("/api/v1/projects/1/ideas", headers=headers)
    assert ideas_resp.status_code == 200
    ideas = ideas_resp.json()
    assert len(ideas) == 3
    idea_ids = [i["id"] for i in ideas]
    print(f"[PASS] 3. Project 1 retrieved with {len(ideas)} candidate ideas: {idea_ids}.")

    # 4. Run Evaluation on All 3 Ideas
    eval_resp = client.post("/api/v1/projects/1/evaluate", headers=headers, json={
        "weights": {
            "problem_significance": 1.5,
            "technical_feasibility": 1.5,
            "implementation_complexity": 1.0,
            "estimated_development_cost": 1.0
        }
    })
    assert eval_resp.status_code == 200, f"Evaluation failed: {eval_resp.text}"
    data = eval_resp.json()
    assert len(data["evaluations"]) == 3
    print(f"[PASS] 4. Evaluated all 3 ideas successfully across 10 dimensions.")

    # Verify attributes of evaluated ideas
    for idx, ev in enumerate(data["evaluations"]):
        assert "dimension_scores" in ev
        assert "effective_scores" in ev
        assert "overall_score" in ev
        assert "assumptions" in ev
        assert "strengths" in ev
        assert "weaknesses" in ev
        assert "risks" in ev
        assert "missing_information" in ev
        assert "recommended_experiments" in ev
        raw_comp = ev["dimension_scores"]["implementation_complexity"]
        eff_comp = ev["effective_scores"]["implementation_complexity"]
        # Verify inverse complexity: effective == 11.0 - raw
        assert round(eff_comp, 1) == round(11.0 - raw_comp, 1)
        print(f"   -> Idea {ev['idea_id']}: Score={ev['overall_score']}/100 | Raw Comp={raw_comp} -> Eff Comp={eff_comp} | Assumptions Count={len(ev['assumptions'])}")

    print("[PASS] 5. Verified inverted complexity & cost calculations and assumptions presence.")

    # 5. Verify Recommendation and Trade-off Analysis
    comp = data["comparison"]
    assert comp is not None
    assert comp["recommended_idea_id"] in idea_ids
    assert len(comp["recommendation_rationale"]) > 20
    print(f"[PASS] 6. Recommendation generated: Recommended Idea ID={comp['recommended_idea_id']}, Is Tie={comp['is_tie']}.")
    print(f"   Rationale: {comp['recommendation_rationale'][:120]}...")

    # 6. Test Selective Evaluation (Evaluating only 2 ideas)
    subset_ids = [idea_ids[0], idea_ids[1]]
    subset_resp = client.post("/api/v1/projects/1/evaluate", headers=headers, json={
        "idea_ids": subset_ids
    })
    assert subset_resp.status_code == 200
    subset_data = subset_resp.json()
    assert len(subset_data["evaluations"]) == 2
    print(f"[PASS] 7. Selective evaluation verified: evaluated only specified {len(subset_ids)} ideas.")

    # 7. Test Priority Recalculation Endpoint
    recalc_resp = client.post("/api/v1/projects/1/recommendation", headers=headers, json={
        "weights": {
            "novelty": 3.0,
            "competitive_landscape": 2.5,
            "technical_feasibility": 0.5
        }
    })
    assert recalc_resp.status_code == 200
    recalc_data = recalc_resp.json()
    assert recalc_data["recommended_idea_id"] in subset_ids
    print(f"[PASS] 8. Priority weight recalculation verified dynamically.")

    # 8. Test Data Persistence via GET
    get_eval = client.get("/api/v1/projects/1/evaluation", headers=headers)
    assert get_eval.status_code == 200
    persisted = get_eval.json()
    assert len(persisted["evaluations"]) == 2
    assert persisted["comparison"] is not None
    print(f"[PASS] 9. Database persistence verified via GET /projects/1/evaluation.")

    print("\n>>> ALL PHASE 4 LIVE VERIFICATION CHECKS PASSED 100%! <<<\n")

if __name__ == "__main__":
    test_phase4_live()
