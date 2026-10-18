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


def test_three_deliberately_different_candidate_ideas_evaluation(client, auth_headers):
    """
    Regression test evaluating three deliberately different candidate ideas:
    1. Hardware/Marine Robotics: Autonomous Solar Catamaran for Microplastics
    2. Healthcare/Clinical AI: Diagnostic Safety Co-Pilot for Pediatric ERs
    3. Retail/SMB SaaS: Bakery Demand & Inventory Forecasting
    Verifies distinct dimension scores, inverse scoring for cost/complexity,
    content-specific strengths/risks, honest evidence provenance, persistence,
    reloading, and weight-driven recommendation shifts.
    """
    proj = client.post("/api/v1/projects/", headers=auth_headers, json={
        "title": "Multi-Candidate Heterogeneous Evaluation Project",
        "description": "Cross-domain venture diligence benchmark"
    }).json()
    proj_id = proj["id"]

    # Candidate 1: Physical Marine Robotics (High complexity, high cost, high novelty, moderate feasibility)
    idea1_payload = {
        "title": "Autonomous Solar Catamaran for Marine Microplastics",
        "problem_statement": "Ocean microplastics smaller than 5mm escape coastal boom nets, causing bioaccumulation in 90% of marine species and costing commercial fisheries $13 billion annually.",
        "proposed_solution": "Autonomous solar-electric catamaran equipped with multi-stage centrifugal filtration, hydrodynamic vortex separation, and satellite telemetry.",
        "target_audience": "Municipal port authorities, oceanic conservation foundations, and coastal environmental ministries",
        "industry": "Environmental Robotics",
        "intended_use_case": "Continuous 24/7 autonomous offshore skimming and microplastic collection in harbor approaches",
        "expected_benefits": "Collects 50kg microplastics per day with zero emissions and 99.4% autonomous navigation uptime.",
        "constraints": "Harsh saltwater corrosion, high wave state survivability (Sea State 4), and battery weight limits.",
        "estimated_budget": "$750,000 for naval architecture testing and prototype catamaran fleet",
        "technical_preferences": "Rust embedded microcontrollers, ROS2, LoRaWAN mesh, carbon-fiber composite hull"
    }

    # Candidate 2: High-Stakes Clinical Healthcare (High significance, strict HIPAA/privacy, high defensibility, physician persona)
    idea2_payload = {
        "title": "AI Clinical Diagnostic Safety Co-Pilot for Pediatric Emergency Rooms",
        "problem_statement": "High-stress pediatric ER triage misclassifies 14% of rare acute systemic inflammatory conditions, leading to delayed interventions and malpractice liabilities averaging $420k per incident.",
        "proposed_solution": "On-premise edge inference co-pilot analyzing vital telemetry, EHR notes, and pediatric triage guidelines to trigger differential diagnostic alerts for sepsis and shock.",
        "target_audience": "Pediatric emergency room physicians, triage nurse managers, and clinical risk officers",
        "industry": "Healthcare & Clinical Medicine",
        "intended_use_case": "Real-time decision support during patient triage and acute resuscitation intake",
        "expected_benefits": "Reduces diagnostic oversight by 62% and cuts time-to-antibiotic in suspected sepsis from 78 minutes to 28 minutes.",
        "constraints": "Strict HIPAA compliance, offline air-gapped hospital network, zero-latency inference (<200ms), and zero hallucination tolerance.",
        "estimated_budget": "$250,000 for clinical study, IRB approvals, and Epic EHR HL7/FHIR integration",
        "technical_preferences": "Local quantized transformers, Python FastAPI backend, HL7 FHIR connectors, air-gapped Linux servers"
    }

    # Candidate 3: Lightweight SMB Web SaaS (Low complexity, low cost, high adoption, SMB self-serve)
    idea3_payload = {
        "title": "Cloud-Based Collaborative Inventory Forecasting SaaS for Independent Bakeries",
        "problem_statement": "Independent craft bakeries discard 18% of fresh inventory daily due to static manual spreadsheet forecasting and weather-driven demand swings, losing $32,000 in gross margin annually.",
        "proposed_solution": "Self-serve B2B SaaS web and mobile dashboard connecting POS sales data (Square, Toast) with hyper-local weather forecasts to predict optimal daily bake volumes.",
        "target_audience": "Independent artisanal bakery owners, pastry chefs, and small food co-op managers",
        "industry": "Retail & Food SaaS",
        "intended_use_case": "Daily 5:00 AM bake sheet generation and weekly ingredient reorder automation",
        "expected_benefits": "Reduces inventory spoilage by 45%, saving $14,000/year per bakery with 15-minute onboarding.",
        "constraints": "Low technical literacy of kitchen staff, tight SMB software budget (<$100/mo), and mobile-friendly offline view.",
        "estimated_budget": "$20,000 bootstrapped MVP budget",
        "technical_preferences": "React web app, PostgreSQL, Python/FastAPI, Toast/Square OAuth APIs, AWS serverless"
    }

    id1 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json=idea1_payload).json()["id"]
    id2 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json=idea2_payload).json()["id"]
    id3 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json=idea3_payload).json()["id"]

    # 1. Run evaluation with balanced default weights
    eval_res = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers)
    assert eval_res.status_code == 200
    data = eval_res.json()

    evals = data["evaluations"]
    assert len(evals) == 3

    eval_by_idea = {e["idea_id"]: e for e in evals}
    ev1 = eval_by_idea[id1]
    ev2 = eval_by_idea[id2]
    ev3 = eval_by_idea[id3]

    # 2. Verify all 10 dimensions exist and are within valid [1.0, 10.0] range
    for ev in [ev1, ev2, ev3]:
        for dim, score in ev["dimension_scores"].items():
            assert 1.0 <= score <= 10.0, f"Dimension {dim} has invalid score: {score}"
        for dim, eff in ev["effective_scores"].items():
            assert 1.0 <= eff <= 10.0, f"Effective dimension {dim} has invalid score: {eff}"

    # 3. Verify Genuine Differences in Dimensional Profiles
    # Marine robotics (Idea 1) must have much higher raw complexity and cost than bakery SaaS (Idea 3)
    assert ev1["dimension_scores"]["implementation_complexity"] > ev3["dimension_scores"]["implementation_complexity"]
    assert ev1["dimension_scores"]["estimated_development_cost"] > ev3["dimension_scores"]["estimated_development_cost"]

    # Consequently, under inverse scoring, bakery SaaS must have HIGHER effective complexity and cost scores
    assert ev3["effective_scores"]["implementation_complexity"] > ev1["effective_scores"]["implementation_complexity"]
    assert ev3["effective_scores"]["estimated_development_cost"] > ev1["effective_scores"]["estimated_development_cost"]

    # Clinical Healthcare (Idea 2) must have highest problem significance due to pediatric mortality/life safety
    assert ev2["dimension_scores"]["problem_significance"] >= 8.5
    assert ev2["dimension_scores"]["target_user_clarity"] >= 7.5

    # Marine robotics must lead in novelty
    assert ev1["dimension_scores"]["novelty"] >= ev3["dimension_scores"]["novelty"]

    # Bakery SaaS must have higher regulatory/privacy compliance safety (no patient records or autonomous drones)
    assert ev3["dimension_scores"]["security_privacy_ethics"] > ev2["dimension_scores"]["security_privacy_ethics"]

    # 4. Verify Content-Specific Textual Insights
    # Strengths must reference each idea's actual solution and audience
    assert "catamaran" in ev1["strengths"][0].lower() or "microplastic" in ev1["strengths"][0].lower()
    assert "triage" in ev2["strengths"][0].lower() or "pediatric" in ev2["strengths"][0].lower() or "diagnostic" in ev2["strengths"][0].lower()
    assert "bakery" in ev3["strengths"][1].lower() or "bake" in ev3["strengths"][0].lower() or "inventory" in ev3["strengths"][0].lower()

    # Risks must be domain-specific
    assert any("marine" in r.lower() or "hardware" in r.lower() or "telemetry" in r.lower() for r in ev1["risks"])
    assert any("clinical" in r.lower() or "hipaa" in r.lower() or "liability" in r.lower() for r in ev2["risks"])
    assert any("churn" in r.lower() or "onboarding" in r.lower() or "smb" in r.lower() or "api" in r.lower() for r in ev3["risks"])

    # Evidence notes must honestly disclose evaluation engine without fabricating empirical claims
    for ev in [ev1, ev2, ev3]:
        assert len(ev["evidence_notes"]) >= 1
        assert "hypotheses" in ev["evidence_notes"][1].lower() or "diligence" in ev["evidence_notes"][1].lower()
        # Ensure no bogus claim that empirical field testing occurred
        assert "does not claim" in str(ev["evidence_notes"]).lower() or "rather than verified empirical" in str(ev["evidence_notes"]).lower()

    # 5. Verify Persistence & Reload Integrity
    get_res = client.get(f"/api/v1/projects/{proj_id}/evaluation", headers=auth_headers)
    assert get_res.status_code == 200
    reloaded_data = get_res.json()
    assert len(reloaded_data["evaluations"]) == 3
    reloaded_by_id = {e["idea_id"]: e for e in reloaded_data["evaluations"]}
    for id_val in [id1, id2, id3]:
        assert reloaded_by_id[id_val]["overall_score"] == eval_by_idea[id_val]["overall_score"]
        assert reloaded_by_id[id_val]["dimension_scores"] == eval_by_idea[id_val]["dimension_scores"]

    # 6. Verify Dynamic Recommendation Shift Under Different Weights
    # Priority A: Emphasize Capital Efficiency and Simplicity (Low cost, low complexity)
    lean_weights = {
        "problem_significance": 1.0, "target_user_clarity": 1.0, "technical_feasibility": 1.5,
        "implementation_complexity": 3.0, "estimated_development_cost": 3.0,
        "adoption_potential": 2.0, "competitive_landscape": 0.5, "novelty": 0.5,
        "security_privacy_ethics": 1.0, "evidence_quality": 1.0
    }
    recalc_lean = client.post(f"/api/v1/projects/{proj_id}/recommendation", headers=auth_headers, json={"weights": lean_weights}).json()
    assert recalc_lean["recommended_idea_id"] == id3, "Bakery SaaS should lead under high capital-efficiency and simplicity weights"

    # Priority B: Emphasize Breakthrough Novelty and Life-Safety Problem Significance
    breakthrough_weights = {
        "problem_significance": 3.0, "target_user_clarity": 1.5, "technical_feasibility": 0.5,
        "implementation_complexity": 0.2, "estimated_development_cost": 0.2,
        "adoption_potential": 0.5, "competitive_landscape": 2.5, "novelty": 3.0,
        "security_privacy_ethics": 0.5, "evidence_quality": 1.0
    }
    recalc_breakthrough = client.post(f"/api/v1/projects/{proj_id}/recommendation", headers=auth_headers, json={"weights": breakthrough_weights}).json()
    assert recalc_breakthrough["recommended_idea_id"] in [id1, id2], "Marine robotics or Pediatric co-pilot should lead under breakthrough novelty & problem significance weights"


def test_identical_candidate_ideas_tie_handling(client, auth_headers):
    """
    Verifies that when two identical ideas are evaluated, the system handles
    the tied scores honestly by detecting identical dimensional profiles
    rather than fabricating arbitrary differentiation.
    """
    proj = client.post("/api/v1/projects/", headers=auth_headers, json={"title": "Identical Pair Project"}).json()
    proj_id = proj["id"]

    same_payload = {
        "title": "Quantum Key Distribution Repeater Node",
        "problem_statement": "Single-photon attenuation limits direct fiber quantum communication to 100km.",
        "proposed_solution": "Cryogenic optical memory repeater nodes utilizing trapped ion entanglement swapping.",
        "target_audience": "Defense telecommunication agencies and national quantum network operators",
        "industry": "Quantum Telecommunications",
        "intended_use_case": "Continental quantum key exchange",
        "expected_benefits": "Extends secure transmission distance to 1000km with zero eavesdropping vulnerability.",
        "constraints": "Sub-Kelvin dilution refrigerators, 1550nm telecom wavelength conversion.",
        "estimated_budget": "$2,000,000 for laboratory prototype",
        "technical_preferences": "Trapped ytterbium ions, ultra-high vacuum chambers"
    }

    id_a = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json=same_payload).json()["id"]
    id_b = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json=same_payload).json()["id"]

    eval_res = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers).json()
    comp = eval_res["comparison"]

    assert comp["is_tie"] == 1
    assert comp["tradeoff_analysis"]["score_difference"] == 0.0
    assert "Identical Composite Scores" in comp["recommendation_rationale"]
    assert comp["tradeoff_analysis"].get("is_identical") is True


def test_reevaluation_stale_refresh_and_candidate_mapping_integrity(client, auth_headers, db):
    """
    Regression test addressing the exact scenario:
    1. Creates a project with 3 candidate ideas.
    2. Injects stale legacy evaluations (e.g. placeholder 74.1 scores with identical dimensions and strings).
    3. Simulates page reload by calling GET /api/v1/projects/{proj_id}/evaluation:
       - Confirms stale evaluations are detected and automatically refreshed.
       - Confirms candidate-specific evaluations are persisted and mapped to correct idea_id.
    4. Simulates Re-Evaluate button by calling POST /api/v1/projects/{proj_id}/evaluate:
       - Confirms request with distinct candidate IDs updates the database.
       - Confirms clean session flush and distinct candidate-specific findings.
    """
    from datetime import datetime, timezone
    from app.models.evaluation import Evaluation, ComparisonResult

    # 1. Create project
    proj = client.post("/api/v1/projects/", headers=auth_headers, json={
        "title": "Autonomous Environmental Systems Benchmark",
        "description": "Multi-candidate diligence test"
    }).json()
    proj_id = proj["id"]

    # 2. Add 3 distinct candidate ideas
    c1 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        "title": "Subterranean LoRa Wildfire Drone Mesh",
        "problem_statement": "Lightning ignites remote forest canopy fires that go undetected for hours.",
        "proposed_solution": "Thermal camera quadcopter fleet relaying telemetry through subterranean LoRa repeaters.",
        "target_audience": "Wildland forestry firefighters and emergency managers",
        "industry": "Disaster Response Robotics",
        "intended_use_case": "Automated lightning strike surveillance",
        "expected_benefits": "Detects smoldering fires within 10 minutes.",
        "constraints": "Sub-zero mountain operations and tree canopy interference",
        "estimated_budget": "$500,000 fleet development budget",
        "technical_preferences": "Embedded C++, ROS2, LoRaWAN"
    }).json()["id"]

    c2 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        "title": "Hospital Sepsis Early-Warning AI Co-Pilot",
        "problem_statement": "Pediatric emergency departments experience delayed diagnosis in acute sepsis cases.",
        "proposed_solution": "Edge transformer analyzing live patient vital signs and EHR labs to trigger differential alerts.",
        "target_audience": "Pediatric triage nurses and emergency physicians",
        "industry": "Healthcare & Clinical Medicine",
        "intended_use_case": "Emergency room patient intake monitoring",
        "expected_benefits": "Reduces diagnostic latency by 50% and improves antibiotic timing.",
        "constraints": "Strict HIPAA compliance and air-gapped hospital intranet",
        "estimated_budget": "$150,000 for clinical trials and IRB clearance",
        "technical_preferences": "FastAPI, PyTorch, HL7 FHIR"
    }).json()["id"]

    c3 = client.post(f"/api/v1/projects/{proj_id}/ideas", headers=auth_headers, json={
        "title": "Artisanal Bakery Inventory Forecasting SaaS",
        "problem_statement": "Independent bakeries waste 20% of fresh pastries due to weather shifts and manual guessing.",
        "proposed_solution": "Web dashboard correlating POS checkout data with hyper-local precipitation forecasts.",
        "target_audience": "Bakery shop owners and pastry chefs",
        "industry": "FoodTech SaaS",
        "intended_use_case": "Daily morning bake volume optimization",
        "expected_benefits": "Cuts unsold inventory spoilage by 40%.",
        "constraints": "Simple non-technical UI and tight SMB software subscription cost (<$50/mo)",
        "estimated_budget": "$15,000 MVP development budget",
        "technical_preferences": "React, FastAPI, SQLite"
    }).json()["id"]

    # 3. Inject stale legacy evaluations (placeholder 74.1 score with static template text)
    db.expire_all()
    stale_scores = {
        "problem_significance": 8.5, "target_user_clarity": 8.0, "technical_feasibility": 8.2,
        "implementation_complexity": 5.2, "estimated_development_cost": 4.8, "adoption_potential": 7.8,
        "competitive_landscape": 7.4, "novelty": 7.2, "security_privacy_ethics": 8.0, "evidence_quality": 7.0
    }
    stale_missing = ["Specific hardware endurance and battery thermal degradation data in sub-zero operational environments."]
    stale_strengths = ["Clear architectural division of responsibilities enabling modular MVP deployment."]
    stale_risks = ["Environmental or technical telemetry dropouts under extreme operational edge conditions."]

    for cid in [c1, c2, c3]:
        stale_ev = Evaluation(
            project_id=proj_id,
            idea_id=cid,
            dimension_scores=stale_scores,
            overall_score=74.1,
            strengths=stale_strengths,
            weaknesses=["Stale weakness"],
            risks=stale_risks,
            assumptions=["Stale assumption"],
            evidence_notes=["Stale notes"],
            missing_information=stale_missing,
            recommended_experiments=["Stale experiment"],
            created_at=datetime.now(timezone.utc)
        )
        db.add(stale_ev)
    db.commit()
    db.close()

    # 4. Simulate page reload: GET /api/v1/projects/{proj_id}/evaluation
    get_res = client.get(f"/api/v1/projects/{proj_id}/evaluation", headers=auth_headers)
    assert get_res.status_code == 200
    reload_data = get_res.json()
    reloaded_evals = reload_data["evaluations"]

    assert len(reloaded_evals) == 3
    reloaded_by_id = {e["idea_id"]: e for e in reloaded_evals}
    assert set(reloaded_by_id.keys()) == {c1, c2, c3}

    # Verify that stale 74.1 scores were replaced with genuine domain-specific assessments
    ev1 = reloaded_by_id[c1]
    ev2 = reloaded_by_id[c2]
    ev3 = reloaded_by_id[c3]

    # Scores must no longer be all 74.1
    scores = [ev1["overall_score"], ev2["overall_score"], ev3["overall_score"]]
    assert not all(s == 74.1 for s in scores), f"Evaluations were not refreshed: {scores}"

    # Verify candidate-specific strengths
    assert any("drone" in s.lower() or "wildfire" in s.lower() or "thermal" in s.lower() for s in ev1["strengths"])
    assert any("sepsis" in s.lower() or "hospital" in s.lower() or "clinical" in s.lower() or "triage" in s.lower() for s in ev2["strengths"])
    assert any("bakery" in s.lower() or "bake" in s.lower() or "inventory" in s.lower() for s in ev3["strengths"])

    # Verify candidate-specific risks
    assert any("hardware" in r.lower() or "telemetry" in r.lower() for r in ev1["risks"])
    assert any("clinical" in r.lower() or "regulatory" in r.lower() or "decision support" in r.lower() for r in ev2["risks"])

    # 5. Simulate Re-Evaluate button: POST /api/v1/projects/{proj_id}/evaluate with explicit candidate IDs
    reeval_res = client.post(f"/api/v1/projects/{proj_id}/evaluate", headers=auth_headers, json={
        "idea_ids": [c1, c2, c3]
    })
    assert reeval_res.status_code == 200
    reeval_data = reeval_res.json()
    assert len(reeval_data["evaluations"]) == 3
    reeval_by_id = {e["idea_id"]: e for e in reeval_data["evaluations"]}

    # Verify persistence: DB must match returned evaluations
    db.expire_all()
    db_evals = db.query(Evaluation).filter(Evaluation.project_id == proj_id).all()
    assert len(db_evals) == 3
    for dbe in db_evals:
        assert dbe.overall_score == reeval_by_id[dbe.idea_id]["overall_score"]
        assert dbe.dimension_scores == reeval_by_id[dbe.idea_id]["dimension_scores"]


