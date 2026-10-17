import pytest
from app.services.scoring_engine import ScoringEngine
from app.models.idea import Idea
from app.models.evaluation import Evaluation


def test_scoring_engine_math_and_weights():
    # If all beneficial dimensions are 8.0 and cost/complexity are 3.0 (meaning low cost/low complexity -> effective 8.0)
    sample_scores = {
        "problem_significance": 8.0,
        "target_user_clarity": 8.0,
        "technical_feasibility": 8.0,
        "implementation_complexity": 3.0,  # Effective = 11.0 - 3.0 = 8.0
        "estimated_development_cost": 3.0,  # Effective = 11.0 - 3.0 = 8.0
        "adoption_potential": 8.0,
        "competitive_landscape": 8.0,
        "novelty": 8.0,
        "security_privacy_ethics": 8.0,
        "evidence_quality": 8.0
    }
    # Equal weights -> (8.0 * 10 / 10) * 10 = 80.0
    overall = ScoringEngine.calculate_overall_score(sample_scores)
    assert overall == 80.0


def test_complexity_and_cost_inversion():
    """Verifies that higher raw complexity and higher raw development cost penalize the composite score."""
    low_friction_scores = {
        "problem_significance": 8.0,
        "technical_feasibility": 8.0,
        "implementation_complexity": 2.0,  # Low complexity -> Effective 9.0
        "estimated_development_cost": 2.0   # Low cost -> Effective 9.0
    }
    high_friction_scores = {
        "problem_significance": 8.0,
        "technical_feasibility": 8.0,
        "implementation_complexity": 9.0,  # High complexity -> Effective 2.0
        "estimated_development_cost": 9.0   # High cost -> Effective 2.0
    }

    score_low = ScoringEngine.calculate_overall_score(low_friction_scores)
    score_high = ScoringEngine.calculate_overall_score(high_friction_scores)

    # Low friction (simple + cheap) must score higher than high friction (complex + expensive)
    assert score_low > score_high
    assert score_low == 85.0   # (8 + 8 + 9 + 9) / 4 * 10 = 85.0
    assert score_high == 50.0  # (8 + 8 + 2 + 2) / 4 * 10 = 50.0

    # Test breakdown details
    breakdown = ScoringEngine.get_scoring_breakdown(low_friction_scores)
    assert breakdown["composite_score"] == 85.0
    dims = {d["dimension"]: d for d in breakdown["dimensions"]}
    assert dims["implementation_complexity"]["is_inverted"] is True
    assert dims["implementation_complexity"]["effective_score"] == 9.0
    assert dims["estimated_development_cost"]["effective_score"] == 9.0


def test_scoring_engine_tie_detection():
    idea1 = Idea(id=1, title="Candidate A", problem_statement="P1", proposed_solution="S1", target_audience="T1", industry="I1", intended_use_case="U1", expected_benefits="B1")
    idea2 = Idea(id=2, title="Candidate B", problem_statement="P2", proposed_solution="S2", target_audience="T2", industry="I2", intended_use_case="U2", expected_benefits="B2")

    scores_a = {
        "problem_significance": 8.0, "target_user_clarity": 8.0, "technical_feasibility": 8.0,
        "implementation_complexity": 3.0, "estimated_development_cost": 3.0, "adoption_potential": 8.0,
        "competitive_landscape": 8.0, "novelty": 8.0, "security_privacy_ethics": 8.0, "evidence_quality": 8.0
    }
    scores_b = {
        "problem_significance": 8.1, "target_user_clarity": 8.0, "technical_feasibility": 8.0,
        "implementation_complexity": 3.0, "estimated_development_cost": 3.0, "adoption_potential": 8.0,
        "competitive_landscape": 8.0, "novelty": 8.0, "security_privacy_ethics": 8.0, "evidence_quality": 8.0
    }

    eval1 = Evaluation(id=101, idea_id=1, dimension_scores=scores_a, overall_score=80.0, strengths=["Execution speed"], weaknesses=[], risks=[], assumptions=[])
    eval2 = Evaluation(id=102, idea_id=2, dimension_scores=scores_b, overall_score=80.1, strengths=["Differentiation"], weaknesses=[], risks=[], assumptions=[])

    result = ScoringEngine.compare_ideas([idea1, idea2], [eval1, eval2])
    assert result["is_tie"] == 1
    assert "Statistical Parity / Close Decision" in result["recommendation_rationale"]
    assert result["tradeoff_analysis"]["score_difference"] < 2.0


def test_insufficient_evidence_inconclusive_flag():
    idea1 = Idea(id=1, title="Candidate A", problem_statement="P1", proposed_solution="S1", target_audience="T1")
    idea2 = Idea(id=2, title="Candidate B", problem_statement="P2", proposed_solution="S2", target_audience="T2")

    # Low evidence quality score (3.0 < 4.5)
    scores_low_ev1 = {"problem_significance": 8.0, "evidence_quality": 3.0}
    scores_low_ev2 = {"problem_significance": 7.0, "evidence_quality": 3.5}

    eval1 = Evaluation(id=1, idea_id=1, dimension_scores=scores_low_ev1, overall_score=55.0, strengths=[], weaknesses=[], risks=[])
    eval2 = Evaluation(id=2, idea_id=2, dimension_scores=scores_low_ev2, overall_score=52.5, strengths=[], weaknesses=[], risks=[])

    res = ScoringEngine.compare_ideas([idea1, idea2], [eval1, eval2])
    assert res["is_tie"] == 1
    assert "Inconclusive Recommendation" in res["recommendation_rationale"]
    assert res["tradeoff_analysis"]["is_inconclusive"] is True


def test_evaluation_api_flow(client, auth_headers):
    # 1. Create project
    proj_res = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Evaluation Flow Test"}).json()
    proj_id = proj_res["id"]

    idea_payload = {
        "problem_statement": "Manual code review takes excessive hours for high-velocity teams.",
        "proposed_solution": "Real-time semantic AST diffing with verifiable compiler checks.",
        "target_audience": "Software engineering leads",
        "industry": "DevOps",
        "intended_use_case": "GitHub PR automated gatekeeper",
        "expected_benefits": "50% reduction in merge review cycle times."
    }

    # 2. Test evaluation when project has zero ideas -> 400 Bad Request
    empty_eval = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers)
    assert empty_eval.status_code == 400

    # 3. Add 3 ideas to project
    res1 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={**idea_payload, "title": "Semantic AST Gatekeeper"}).json()
    res2 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={**idea_payload, "title": "Test Mutation Synthesizer"}).json()
    res3 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={**idea_payload, "title": "Contract Fuzzing Engine"}).json()

    idea_ids = [res1["id"], res2["id"], res3["id"]]

    # 4. Test selective idea evaluation (selecting 2 ideas out of 3)
    sel_res = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers, json={
        "idea_ids": [idea_ids[0], idea_ids[1]]
    })
    assert sel_res.status_code == 200
    sel_data = sel_res.json()
    assert len(sel_data["evaluations"]) == 2
    assert "assumptions" in sel_data["evaluations"][0]
    assert "effective_scores" in sel_data["evaluations"][0]
    assert "formula_explanation" in sel_data

    # 5. Test invalid idea_ids (too many > 3 or non-existent ID)
    bad_res1 = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers, json={
        "idea_ids": [idea_ids[0], idea_ids[1], idea_ids[2], 9999]
    })
    assert bad_res1.status_code == 400

    bad_res2 = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers, json={
        "idea_ids": [999999]
    })
    assert bad_res2.status_code == 400

    # 6. Evaluate all 3 ideas with custom weights
    all_eval = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers, json={
        "weights": {
            "problem_significance": 2.0,
            "technical_feasibility": 2.0,
            "implementation_complexity": 1.5,
            "estimated_development_cost": 1.5
        }
    })
    assert all_eval.status_code == 200
    all_data = all_eval.json()
    assert len(all_data["evaluations"]) == 3
    assert all_data["comparison"] is not None
    assert all_data["comparison"]["recommended_idea_id"] in idea_ids

    # 7. GET current evaluations
    get_res = client.get(f"/api/v1/projects/{proj_id}/evaluation", headers=auth_headers)
    assert get_res.status_code == 200
    assert len(get_res.json()["evaluations"]) == 3

    # 8. Re-calculate recommendation with dynamic weights
    recalc_res = client.post(f"/api/v1/projects/{proj_id}/recommendation", headers=auth_headers, json={
        "weights": {
            "technical_feasibility": 3.0,
            "novelty": 0.5,
            "estimated_development_cost": 2.0
        }
    })
    assert recalc_res.status_code == 200
    assert "recommendation_rationale" in recalc_res.json()


def test_evaluation_user_isolation(client, auth_headers):
    """Verifies that an unauthorized user cannot evaluate or view another user's project."""
    # User 1 creates project
    proj = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Private Research"}).json()
    proj_id = proj["id"]

    # Register User 2
    user2_reg = client.post("/api/v1/auth/register", json={
        "email": "intruder_user@idealens.ai",
        "password": "Password123!",
        "full_name": "Intruder User"
    })
    token2 = user2_reg.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {token2}"}

    # User 2 attempts to evaluate User 1's project -> 403 Forbidden
    eval_attempt = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=user2_headers)
    assert eval_attempt.status_code == 403

    # User 2 attempts to view User 1's evaluation -> 403 Forbidden
    view_attempt = client.get(f"/api/v1/projects/{proj_id}/evaluation", headers=user2_headers)
    assert view_attempt.status_code == 403
