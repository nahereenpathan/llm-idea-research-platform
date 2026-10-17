import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.models.project import Project
from app.models.idea import Idea
from app.models.evaluation import Evaluation, ComparisonResult
from app.schemas.evaluation import (
    ComparisonRequest, ComparisonResultOut, EvaluationOut,
    FullProjectEvaluationResponse, DimensionWeights
)
from app.api.v1.deps import verify_project_ownership
from app.services.ai.factory import get_llm_provider
from app.services.scoring_engine import ScoringEngine

router = APIRouter()


@router.post("/projects/{project_id}/evaluate", response_model=FullProjectEvaluationResponse)
def evaluate_project_ideas(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Evaluates each idea in the project on 10 explicit dimensions, computes explainable composite scores,
    identifies strengths/risks, and derives transparent comparative rankings.
    """
    ideas = db.query(Idea).filter(Idea.project_id == project.id).all()
    if not ideas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot run evaluation: no ideas have been submitted to this project yet."
        )

    llm = get_llm_provider()

    # Clear previous evaluations for a fresh run
    db.query(Evaluation).filter(Evaluation.project_id == project.id).delete()
    db.query(ComparisonResult).filter(ComparisonResult.project_id == project.id).delete()

    created_evals = []
    for idea in ideas:
        prompt = (
            f"Idea Evaluation Request:\n"
            f"Title: {idea.title}\n"
            f"Problem Statement: {idea.problem_statement}\n"
            f"Proposed Solution: {idea.proposed_solution}\n"
            f"Target Audience: {idea.target_audience}\n"
            f"Industry: {idea.industry}\n"
            f"Intended Use Case: {idea.intended_use_case}\n"
            f"Expected Benefits: {idea.expected_benefits}\n"
            f"Constraints: {idea.constraints or 'None specified'}\n"
            f"Budget: {idea.estimated_budget or 'Not specified'}\n"
            f"Technical Preferences: {idea.technical_preferences or 'None'}\n\n"
            "Score on 1-10 scale for:\n"
            "1. problem_significance\n"
            "2. target_user_clarity\n"
            "3. technical_feasibility\n"
            "4. implementation_complexity\n"
            "5. estimated_development_cost\n"
            "6. adoption_potential\n"
            "7. competitive_landscape\n"
            "8. novelty\n"
            "9. security_privacy_ethics\n"
            "10. evidence_quality\n"
            "Also return strengths, weaknesses, risks, evidence_notes, missing_information, and recommended_experiments."
        )

        sys_prompt = (
            "You are an expert technology diligence assessor and venture research architect. "
            "Evaluate realistically. Never claim AI can predict guaranteed future success. "
            "Distinguish evidence-backed assessments from assumptions."
        )

        try:
            eval_data = llm.generate_structured(prompt, sys_prompt)
        except Exception:
            # Fallback to local heuristic evaluator if external provider errors
            from app.services.ai.heuristic_provider import HeuristicFallbackProvider
            eval_data = HeuristicFallbackProvider().generate_structured(prompt, sys_prompt)

        dim_scores = eval_data.get("dimension_scores", {})
        # Ensure all 10 dimensions exist with valid float values
        standard_dims = [
            "problem_significance", "target_user_clarity", "technical_feasibility",
            "implementation_complexity", "estimated_development_cost", "adoption_potential",
            "competitive_landscape", "novelty", "security_privacy_ethics", "evidence_quality"
        ]
        clean_dims = {}
        for d in standard_dims:
            val = dim_scores.get(d, 7.0)
            clean_dims[d] = max(1.0, min(10.0, float(val)))

        overall_score = ScoringEngine.calculate_overall_score(clean_dims)

        evaluation = Evaluation(
            project_id=project.id,
            idea_id=idea.id,
            dimension_scores=clean_dims,
            overall_score=overall_score,
            strengths=eval_data.get("strengths", ["Clear target problem."]),
            weaknesses=eval_data.get("weaknesses", ["Requires validation of willingness to pay."]),
            risks=eval_data.get("risks", ["Adoption velocity risk."]),
            evidence_notes=eval_data.get("evidence_notes", ["Based on submitted specification."]),
            missing_information=eval_data.get("missing_information", ["User acquisition benchmarks."]),
            recommended_experiments=eval_data.get("recommended_experiments", ["Prototype testing."]),
            created_at=datetime.now(timezone.utc)
        )
        db.add(evaluation)
        created_evals.append(evaluation)

    db.commit()
    for ev in created_evals:
        db.refresh(ev)

    # Perform comparison
    default_weights = DimensionWeights().model_dump()
    comp_result_data = ScoringEngine.compare_ideas(ideas, created_evals, default_weights)

    comp_result = ComparisonResult(
        project_id=project.id,
        configured_weights=default_weights,
        recommended_idea_id=comp_result_data.get("recommended_idea_id"),
        recommendation_rationale=comp_result_data.get("recommendation_rationale", ""),
        tradeoff_analysis=comp_result_data.get("tradeoff_analysis", {}),
        is_tie=comp_result_data.get("is_tie", 0),
        created_at=datetime.now(timezone.utc)
    )
    db.add(comp_result)
    db.commit()
    db.refresh(comp_result)

    return FullProjectEvaluationResponse(
        evaluations=[EvaluationOut.model_validate(e) for e in created_evals],
        comparison=ComparisonResultOut.model_validate(comp_result),
        ideas=[{"id": i.id, "title": i.title, "is_selected": i.is_selected} for i in ideas]
    )


@router.get("/projects/{project_id}/evaluation", response_model=FullProjectEvaluationResponse)
def get_project_evaluations(
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """Retrieves current evaluations and comparison results for the project."""
    evals = db.query(Evaluation).filter(Evaluation.project_id == project.id).all()
    comp = db.query(ComparisonResult).filter(ComparisonResult.project_id == project.id).order_by(ComparisonResult.created_at.desc()).first()
    ideas = db.query(Idea).filter(Idea.project_id == project.id).all()

    return FullProjectEvaluationResponse(
        evaluations=[EvaluationOut.model_validate(e) for e in evals],
        comparison=ComparisonResultOut.model_validate(comp) if comp else None,
        ideas=[{"id": i.id, "title": i.title, "is_selected": i.is_selected} for i in ideas]
    )


@router.post("/projects/{project_id}/recommendation", response_model=ComparisonResultOut)
def recalculate_recommendation_with_weights(
    req: ComparisonRequest,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Dynamically recalculates idea rankings, composite scores, and recommendations
    based on custom user-configured dimension weights.
    """
    ideas = db.query(Idea).filter(Idea.project_id == project.id).all()
    evals = db.query(Evaluation).filter(Evaluation.project_id == project.id).all()
    if not evals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has not been evaluated yet. Run evaluate first."
        )

    weights_dict = req.weights.model_dump() if req.weights else DimensionWeights().model_dump()
    comp_result_data = ScoringEngine.compare_ideas(ideas, evals, weights_dict)

    comp_result = ComparisonResult(
        project_id=project.id,
        configured_weights=weights_dict,
        recommended_idea_id=comp_result_data.get("recommended_idea_id"),
        recommendation_rationale=comp_result_data.get("recommendation_rationale", ""),
        tradeoff_analysis=comp_result_data.get("tradeoff_analysis", {}),
        is_tie=comp_result_data.get("is_tie", 0),
        created_at=datetime.now(timezone.utc)
    )
    db.add(comp_result)
    db.commit()
    db.refresh(comp_result)
    return comp_result
