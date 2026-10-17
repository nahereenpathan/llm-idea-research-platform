from app.services.scoring_engine import ScoringEngine
from app.models.idea import Idea
from app.models.evaluation import Evaluation


def test_scoring_engine_math_and_weights():
    sample_scores = {
        "problem_significance": 8.0,
        "target_user_clarity": 8.0,
        "technical_feasibility": 8.0,
        "implementation_complexity": 8.0,
        "estimated_development_cost": 8.0,
        "adoption_potential": 8.0,
        "competitive_landscape": 8.0,
        "novelty": 8.0,
        "security_privacy_ethics": 8.0,
        "evidence_quality": 8.0
    }
    # Equal weights -> 8.0 * 10 = 80.0
    overall = ScoringEngine.calculate_overall_score(sample_scores)
    assert overall == 80.0

    # Test custom weights: heavy emphasis on novelty (10.0 score) vs cost (5.0 score)
    custom_scores = {
        "novelty": 10.0,
        "estimated_development_cost": 5.0
    }
    # If weights are equal (1, 1): avg is 7.5 -> 75.0
    assert ScoringEngine.calculate_overall_score(custom_scores, {"novelty": 1.0, "estimated_development_cost": 1.0}) == 75.0

    # If novelty weight is 3.0, cost weight is 1.0: (30 + 5) / 4 = 8.75 -> 87.5
    assert ScoringEngine.calculate_overall_score(custom_scores, {"novelty": 3.0, "estimated_development_cost": 1.0}) == 87.5


def test_scoring_engine_tie_detection():
    # Construct 2 mock ideas with close scores (< 2.0 point delta)
    idea1 = Idea(id=1, title="Candidate A", problem_statement="P1", proposed_solution="S1", target_audience="T1", industry="I1", intended_use_case="U1", expected_benefits="B1")
    idea2 = Idea(id=2, title="Candidate B", problem_statement="P2", proposed_solution="S2", target_audience="T2", industry="I2", intended_use_case="U2", expected_benefits="B2")

    scores_a = {f"dim_{i}": 8.0 for i in range(10)}
    scores_b = {f"dim_{i}": 8.1 for i in range(10)}  # Diff is 1.0 point on 100 pt scale

    eval1 = Evaluation(id=101, idea_id=1, dimension_scores=scores_a, overall_score=80.0, strengths=["Execution speed"], weaknesses=[], risks=[])
    eval2 = Evaluation(id=102, idea_id=2, dimension_scores=scores_b, overall_score=81.0, strengths=["Differentiation"], weaknesses=[], risks=[])

    result = ScoringEngine.compare_ideas([idea1, idea2], [eval1, eval2])
    assert result["is_tie"] == 1
    assert "Statistical Parity / Close Decision" in result["recommendation_rationale"]


def test_evaluation_api_flow(client, auth_headers):
    # Create project and 2 ideas
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

    client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={**idea_payload, "title": "Semantic AST Gatekeeper"})
    client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={**idea_payload, "title": "Test Mutation Synthesizer"})

    # Run evaluation
    eval_res = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers)
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert len(data["evaluations"]) == 2
    assert data["comparison"] is not None
    assert "recommended_idea_id" in data["comparison"]

    # Re-calculate recommendation with custom weights
    recalc_res = client.post(f"/api/v1/projects/{proj_id}/recommendation", headers=auth_headers, json={
        "weights": {
            "technical_feasibility": 3.0,
            "novelty": 0.5,
            "estimated_development_cost": 2.0
        }
    })
    assert recalc_res.status_code == 200
    assert "recommendation_rationale" in recalc_res.json()
