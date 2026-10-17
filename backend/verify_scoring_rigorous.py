import httpx
from app.services.scoring_engine import ScoringEngine
from app.services.ai.heuristic_provider import HeuristicFallbackProvider

def run_rigorous_audit():
    print("=== STARTING RIGOROUS SCORING & BACKEND AUDIT ===")

    # 1. Determinism Test
    scores_test = {
        "problem_significance": 8.4,
        "target_user_clarity": 7.9,
        "technical_feasibility": 8.1,
        "implementation_complexity": 4.5,
        "estimated_development_cost": 3.8,
        "adoption_potential": 7.2,
        "competitive_landscape": 6.9,
        "novelty": 7.5,
        "security_privacy_ethics": 8.8,
        "evidence_quality": 6.5
    }
    weights_test = {
        "problem_significance": 1.5,
        "target_user_clarity": 1.0,
        "technical_feasibility": 2.0,
        "implementation_complexity": 1.2,
        "estimated_development_cost": 1.0,
        "adoption_potential": 1.0,
        "competitive_landscape": 1.0,
        "novelty": 1.0,
        "security_privacy_ethics": 1.0,
        "evidence_quality": 1.0
    }
    first_score = ScoringEngine.calculate_overall_score(scores_test, weights_test)
    for _ in range(50):
        s = ScoringEngine.calculate_overall_score(scores_test, weights_test)
        assert s == first_score, f"Non-deterministic score: {s} != {first_score}"
    print(f"[PASS] 1. Determinism confirmed: 50 iterations produced identical score: {first_score}/100.")

    # 2. Weight Normalization Test
    # Doubling all weights should produce the exact same composite score
    weights_doubled = {k: v * 2.0 for k, v in weights_test.items()}
    score_doubled = ScoringEngine.calculate_overall_score(scores_test, weights_doubled)
    assert score_doubled == first_score, f"Weight normalization failed: {score_doubled} != {first_score}"
    print(f"[PASS] 2. Weight normalization confirmed: scaled weights produce identical composite score: {score_doubled}/100.")

    # 3. Monotonic Inversion of Cost & Complexity Test
    base_scores = {
        "problem_significance": 8.0,
        "target_user_clarity": 8.0,
        "technical_feasibility": 8.0,
        "adoption_potential": 8.0,
        "competitive_landscape": 8.0,
        "novelty": 8.0,
        "security_privacy_ethics": 8.0,
        "evidence_quality": 8.0,
        "implementation_complexity": 1.0,
        "estimated_development_cost": 1.0
    }
    prev_score = 100.0
    for complexity_level in [1.0, 3.0, 5.0, 7.0, 9.0, 10.0]:
        test_s = dict(base_scores)
        test_s["implementation_complexity"] = complexity_level
        test_s["estimated_development_cost"] = complexity_level
        comp_score = ScoringEngine.calculate_overall_score(test_s)
        assert comp_score <= prev_score, f"Complexity increase did not reduce score: {comp_score} > {prev_score}"
        prev_score = comp_score
        print(f"   -> Raw Complexity & Cost: {complexity_level:4.1f} | Composite Score: {comp_score:5.1f}/100")

    print("[PASS] 3. Inversion confirmed: higher raw complexity/cost monotonically reduces composite score.")

    # 4. Zero and Negative Weights Resilience
    zero_weights = {k: 0.0 for k in base_scores}
    assert ScoringEngine.calculate_overall_score(base_scores, zero_weights) == 0.0
    negative_weights = {"problem_significance": -5.0, "technical_feasibility": 1.0}
    neg_score = ScoringEngine.calculate_overall_score(base_scores, negative_weights)
    assert 0.0 <= neg_score <= 100.0
    print("[PASS] 4. Edge weights resilience confirmed (zero weights -> 0.0, negative weights clamped safely).")

    # 5. Live API Audit
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15.0)

    # Login
    auth_res = client.post("/api/v1/auth/login", json={
        "email": "researcher_mvp@idealens.ai",
        "password": "SecurePassword123!"
    })
    assert auth_res.status_code == 200
    token = auth_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify project 1
    proj_res = client.get("/api/v1/projects/1", headers=headers)
    assert proj_res.status_code == 200
    print("[PASS] 5. User authorized and project retrieved.")

    # 6. Evaluation with full payload
    eval_req = {
        "idea_ids": [1, 2, 3],
        "weights": {
            "problem_significance": 1.2,
            "target_user_clarity": 1.0,
            "technical_feasibility": 1.5,
            "implementation_complexity": 1.0,
            "estimated_development_cost": 1.0,
            "adoption_potential": 1.0,
            "competitive_landscape": 1.0,
            "novelty": 1.2,
            "security_privacy_ethics": 1.0,
            "evidence_quality": 1.0
        }
    }
    eval_run = client.post("/api/v1/projects/1/evaluate", headers=headers, json=eval_req)
    assert eval_run.status_code == 200
    eval_data = eval_run.json()

    assert len(eval_data["evaluations"]) == 3
    assert eval_data["comparison"] is not None
    assert "formula_explanation" in eval_data
    print(f"[PASS] 6. Live evaluation API executed successfully. Comparison: ID={eval_data['comparison']['recommended_idea_id']}")

    # 7. Persistence Check
    persisted = client.get("/api/v1/projects/1/evaluation", headers=headers)
    assert persisted.status_code == 200
    p_data = persisted.json()
    assert len(p_data["evaluations"]) == 3
    # Check all fields in persisted evaluations
    sample_ev = p_data["evaluations"][0]
    for key in ["id", "project_id", "idea_id", "dimension_scores", "effective_scores", "overall_score", "strengths", "weaknesses", "risks", "assumptions", "missing_information", "recommended_experiments"]:
        assert key in sample_ev, f"Missing key '{key}' in persisted evaluation"
    print("[PASS] 7. Database persistence verified: all fields including assumptions and effective_scores intact.")

    print("\n=== ALL RIGOROUS SCORING AND BACKEND AUDIT CHECKS PASSED 100% ===\n")

if __name__ == "__main__":
    run_rigorous_audit()
