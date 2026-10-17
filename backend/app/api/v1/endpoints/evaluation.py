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
    FullProjectEvaluationResponse, DimensionWeights, EvaluationStartRequest
)
from app.api.v1.deps import verify_project_ownership
from app.services.ai.factory import get_llm_provider
from app.services.scoring_engine import ScoringEngine

router = APIRouter()


@router.post("/projects/{project_id}/evaluate", response_model=FullProjectEvaluationResponse)
def evaluate_project_ideas(
    req: Optional[EvaluationStartRequest] = None,
    project: Project = Depends(verify_project_ownership),
    db: Session = Depends(get_db)
):
    """
    Evaluates selected ideas (up to 3) in the project across 10 explicit dimensions.
    Computes explainable composite scores, inverts cost & complexity, captures assumptions,
    identifies strengths/risks, and derives transparent comparative rankings.
    """
    if req and req.idea_ids:
        if len(req.idea_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must specify at least one idea to evaluate."
            )
        if len(req.idea_ids) > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot evaluate more than 3 candidate ideas simultaneously."
            )
        ideas = db.query(Idea).filter(
            Idea.project_id == project.id,
            Idea.id.in_(req.idea_ids)
        ).all()
        if len(ideas) != len(req.idea_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more specified idea IDs do not belong to this project."
            )
    else:
        ideas = db.query(Idea).filter(Idea.project_id == project.id).all()
        if not ideas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot run evaluation: no ideas have been submitted to this project yet."
            )
        if len(ideas) > 3:
            ideas = ideas[:3]

    weights_dict = req.weights.model_dump() if (req and req.weights) else DimensionWeights().model_dump()
    llm = get_llm_provider()

    # Clear previous evaluations for this project for a fresh comparison run
    db.query(Evaluation).filter(
        Evaluation.project_id == project.id
    ).delete(synchronize_session=False)
    db.query(ComparisonResult).filter(ComparisonResult.project_id == project.id).delete(synchronize_session=False)

    created_evals = []
    standard_dims = [
        "problem_significance", "target_user_clarity", "technical_feasibility",
        "implementation_complexity", "estimated_development_cost", "adoption_potential",
        "competitive_landscape", "novelty", "security_privacy_ethics", "evidence_quality"
    ]

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
            "Score on 1.0-10.0 scale for:\n"
            "1. problem_significance (1 = trivial, 10 = critical urgent problem)\n"
            "2. target_user_clarity (1 = vague, 10 = razor sharp persona)\n"
            "3. technical_feasibility (1 = speculative breakthrough needed, 10 = mature proven stack)\n"
            "4. implementation_complexity (1 = low complexity/easy, 10 = extreme technical hurdles)\n"
            "5. estimated_development_cost (1 = minimal budget, 10 = capital intensive)\n"
            "6. adoption_potential (1 = high resistance, 10 = frictionless adoption)\n"
            "7. competitive_landscape (1 = crowded commodity, 10 = strong defensibility)\n"
            "8. novelty (1 = copycat, 10 = distinctive innovation)\n"
            "9. security_privacy_ethics (1 = severe risks, 10 = safe & compliant)\n"
            "10. evidence_quality (1 = purely speculative, 10 = verified user data)\n\n"
            "Return JSON with: dimension_scores, strengths, weaknesses, risks, assumptions, "
            "evidence_notes, missing_information, and recommended_experiments."
        )

        sys_prompt = (
            "You are an expert technology diligence assessor and venture research architect. "
            "Evaluate realistically. Never claim AI can predict guaranteed future success. "
            "Distinguish evidence-backed assessments from speculative assumptions."
        )

        try:
            eval_data = llm.generate_structured(prompt, sys_prompt)
        except Exception:
            from app.services.ai.heuristic_provider import HeuristicFallbackProvider
            eval_data = HeuristicFallbackProvider().generate_structured(prompt, sys_prompt)

        dim_scores = eval_data.get("dimension_scores", {})
        clean_dims = {}
        for d in standard_dims:
            val = dim_scores.get(d, 7.0)
            clean_dims[d] = max(1.0, min(10.0, float(val)))

        overall_score = ScoringEngine.calculate_overall_score(clean_dims, weights_dict)

        evaluation = Evaluation(
            project_id=project.id,
            idea_id=idea.id,
            dimension_scores=clean_dims,
            overall_score=overall_score,
            strengths=eval_data.get("strengths", ["Clear target problem."]),
            weaknesses=eval_data.get("weaknesses", ["Requires validation of willingness to pay."]),
            risks=eval_data.get("risks", ["Adoption velocity risk."]),
            assumptions=eval_data.get("assumptions", ["Assumes standard API availability."]),
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
    comp_result_data = ScoringEngine.compare_ideas(ideas, created_evals, weights_dict)

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

    # Attach effective scores to output evaluations
    eval_outs = []
    for ev in created_evals:
        eff_scores = {
            dim: ScoringEngine.get_effective_dimension_score(dim, raw)
            for dim, raw in ev.dimension_scores.items()
        }
        ev_out = EvaluationOut.model_validate(ev)
        ev_out.effective_scores = eff_scores
        eval_outs.append(ev_out)

    sample_breakdown = ScoringEngine.get_scoring_breakdown(
        created_evals[0].dimension_scores if created_evals else {},
        weights_dict
    )

    return FullProjectEvaluationResponse(
        evaluations=eval_outs,
        comparison=ComparisonResultOut.model_validate(comp_result),
        ideas=[{"id": i.id, "title": i.title, "is_selected": i.is_selected} for i in ideas],
        formula_explanation={
            "formula": sample_breakdown.get("formula_explanation", ""),
            "inverted_dimensions": list(ScoringEngine.INVERTED_DIMENSIONS),
            "disclaimer": "Ratings are heuristic diligence estimates designed to guide validation experiments, not objective guarantees of market success."
        }
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

    eval_outs = []
    for ev in evals:
        eff_scores = {
            dim: ScoringEngine.get_effective_dimension_score(dim, raw)
            for dim, raw in ev.dimension_scores.items()
        }
        ev_out = EvaluationOut.model_validate(ev)
        ev_out.effective_scores = eff_scores
        eval_outs.append(ev_out)

    weights_dict = comp.configured_weights if comp else DimensionWeights().model_dump()
    sample_breakdown = ScoringEngine.get_scoring_breakdown(
        evals[0].dimension_scores if evals else {},
        weights_dict
    )

    return FullProjectEvaluationResponse(
        evaluations=eval_outs,
        comparison=ComparisonResultOut.model_validate(comp) if comp else None,
        ideas=[{"id": i.id, "title": i.title, "is_selected": i.is_selected} for i in ideas],
        formula_explanation={
            "formula": sample_breakdown.get("formula_explanation", ""),
            "inverted_dimensions": list(ScoringEngine.INVERTED_DIMENSIONS),
            "disclaimer": "Ratings are heuristic diligence estimates designed to guide validation experiments, not objective guarantees of market success."
        }
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

    # Filter ideas to those that have evaluations
    eval_idea_ids = {e.idea_id for e in evals}
    evaluated_ideas = [i for i in ideas if i.id in eval_idea_ids]

    weights_dict = req.weights.model_dump() if req.weights else DimensionWeights().model_dump()
    comp_result_data = ScoringEngine.compare_ideas(evaluated_ideas, evals, weights_dict)

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
