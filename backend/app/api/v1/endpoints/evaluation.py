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
        found_ideas = db.query(Idea).filter(
            Idea.project_id == project.id,
            Idea.id.in_(req.idea_ids)
        ).all()
        if len(found_ideas) != len(req.idea_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more specified idea IDs do not belong to this project."
            )
        idea_map = {i.id: i for i in found_ideas}
        ideas = [idea_map[iid] for iid in req.idea_ids if iid in idea_map]
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
    db.query(Evaluation).filter(Evaluation.project_id == project.id).delete(synchronize_session="fetch")
    db.query(ComparisonResult).filter(ComparisonResult.project_id == project.id).delete(synchronize_session="fetch")
    db.commit()
    db.expire_all()

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
            "Score on 1.0-10.0 scale for each of these 10 dimensions:\n"
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
            "NOTE: implementation_complexity and estimated_development_cost are RAW friction ratings (10 = highest hurdle). "
            "Our scoring formula inverts them so lower complexity and lower cost yield higher overall feasibility.\n\n"
            "Return JSON with: dimension_scores, strengths, weaknesses, risks, assumptions, "
            "evidence_notes, missing_information, and recommended_experiments."
        )

        sys_prompt = (
            "You are an expert technology diligence assessor and venture research architect. "
            "Evaluate realistically based strictly on the candidate's submitted parameters. "
            "Never claim AI can predict guaranteed future success. Distinguish evidence-backed assessments from speculative assumptions."
        )

        # Baseline evaluation from heuristic engine derived directly from candidate idea's specific parameters
        from app.services.ai.heuristic_provider import HeuristicFallbackProvider
        heuristic_engine = HeuristicFallbackProvider()
        fallback_data = heuristic_engine.evaluate_idea(idea)

        eval_data = None
        eval_method_label = "IdeaLens Domain Heuristic Engine"

        if hasattr(llm, "generate_structured") and not isinstance(llm, HeuristicFallbackProvider):
            try:
                ai_data = llm.generate_structured(prompt, sys_prompt)
                if isinstance(ai_data, dict) and "dimension_scores" in ai_data:
                    eval_data = ai_data
                    provider_name = llm.__class__.__name__.replace("Provider", "")
                    model_name = getattr(llm, "model", "")
                    eval_method_label = f"{provider_name} AI ({model_name})" if model_name else f"{provider_name} AI"
            except Exception as e:
                import logging
                logging.getLogger("idealens").warning(f"AI provider evaluation failed for idea {idea.id} ('{idea.title}'): {e}. Using heuristic engine.")

        if not eval_data:
            eval_data = fallback_data

        dim_scores = eval_data.get("dimension_scores", {})
        clean_dims = {}
        for d in standard_dims:
            val = dim_scores.get(d)
            if val is None or not isinstance(val, (int, float)):
                val = fallback_data["dimension_scores"].get(d, 6.5)
            clean_dims[d] = round(max(1.0, min(10.0, float(val))), 1)

        overall_score = ScoringEngine.calculate_overall_score(clean_dims, weights_dict)

        # Honest evidence notes disclosing the true evaluation engine used
        if "AI" in eval_method_label:
            notes = [
                f"Evaluated via {eval_method_label} based on candidate proposal specifications.",
                "Ratings represent model-assisted diligence estimates designed to guide experiments, not guaranteed market outcomes."
            ]
        else:
            notes = [
                f"Evaluated via {eval_method_label} (no external LLM API active). Analysis derived strictly from submitted specifications for '{idea.title}' ({idea.industry}).",
                "Ratings represent structured diligence hypotheses rather than verified empirical market outcomes."
            ]

        evaluation = Evaluation(
            project_id=project.id,
            idea_id=idea.id,
            dimension_scores=clean_dims,
            overall_score=overall_score,
            strengths=eval_data.get("strengths") or fallback_data["strengths"],
            weaknesses=eval_data.get("weaknesses") or fallback_data["weaknesses"],
            risks=eval_data.get("risks") or fallback_data["risks"],
            assumptions=eval_data.get("assumptions") or fallback_data["assumptions"],
            evidence_notes=notes,
            missing_information=eval_data.get("missing_information") or fallback_data["missing_information"],
            recommended_experiments=eval_data.get("recommended_experiments") or fallback_data["recommended_experiments"],
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

    # Determine if existing evaluations need refresh
    should_refresh = False
    idea_ids_set = {i.id for i in ideas}
    eval_idea_ids = {e.idea_id for e in evals}

    if ideas and not evals:
        # Ideas exist but project hasn't been evaluated yet
        should_refresh = True
    elif ideas and len(evals) != len(ideas):
        # Evaluation count doesn't match idea count
        should_refresh = True
    elif ideas and eval_idea_ids != idea_ids_set:
        # Evaluation idea IDs don't match project idea IDs
        should_refresh = True
    elif evals:
        for e in evals:
            str_repr = (
                str(e.strengths) + " " +
                str(e.risks) + " " +
                str(e.assumptions) + " " +
                str(e.missing_information)
            )
            if (
                e.overall_score == 74.1 or
                "battery thermal degradation" in str_repr or
                "sub-zero" in str_repr or
                "urgent operational bottleneck with clear quantifiable impact" in str_repr or
                "Clear architectural division of responsibilities" in str_repr or
                "telemetry dropouts under extreme operational edge conditions" in str_repr or
                "target enterprise/agency buyers have discretionary budget" in str_repr
            ):
                should_refresh = True
                break

        # Check for suspicious identical scores across distinct ideas
        if not should_refresh and len(evals) > 1 and len(ideas) > 1:
            first_dims = evals[0].dimension_scores
            first_score = evals[0].overall_score
            all_identical = all(e.overall_score == first_score and e.dimension_scores == first_dims for e in evals)
            ideas_distinct = any(
                ideas[i].title != ideas[0].title or ideas[i].problem_statement != ideas[0].problem_statement
                for i in range(1, len(ideas))
            )
            if all_identical and ideas_distinct:
                should_refresh = True

    if should_refresh and ideas:
        from app.services.ai.heuristic_provider import HeuristicFallbackProvider
        heuristic_engine = HeuristicFallbackProvider()
        weights_dict = comp.configured_weights if comp else DimensionWeights().model_dump()
        standard_dims = [
            "problem_significance", "target_user_clarity", "technical_feasibility",
            "implementation_complexity", "estimated_development_cost", "adoption_potential",
            "competitive_landscape", "novelty", "security_privacy_ethics", "evidence_quality"
        ]

        # Cleanly wipe previous evaluations and comparison
        db.query(Evaluation).filter(Evaluation.project_id == project.id).delete(synchronize_session="fetch")
        db.query(ComparisonResult).filter(ComparisonResult.project_id == project.id).delete(synchronize_session="fetch")
        db.commit()
        db.expire_all()

        created_evals = []
        for idea in ideas:
            fallback_data = heuristic_engine.evaluate_idea(idea)
            clean_dims = {}
            for d in standard_dims:
                val = fallback_data["dimension_scores"].get(d, 6.5)
                clean_dims[d] = round(max(1.0, min(10.0, float(val))), 1)

            overall_score = ScoringEngine.calculate_overall_score(clean_dims, weights_dict)
            notes = [
                f"Evaluated via IdeaLens Domain Heuristic Engine (no external LLM API active). Analysis derived strictly from submitted specifications for '{idea.title}' ({idea.industry}).",
                "Ratings represent structured diligence hypotheses rather than verified empirical market outcomes."
            ]

            evaluation = Evaluation(
                project_id=project.id,
                idea_id=idea.id,
                dimension_scores=clean_dims,
                overall_score=overall_score,
                strengths=fallback_data["strengths"],
                weaknesses=fallback_data["weaknesses"],
                risks=fallback_data["risks"],
                assumptions=fallback_data["assumptions"],
                evidence_notes=notes,
                missing_information=fallback_data["missing_information"],
                recommended_experiments=fallback_data["recommended_experiments"],
                created_at=datetime.now(timezone.utc)
            )
            db.add(evaluation)
            created_evals.append(evaluation)

        db.commit()
        for ev in created_evals:
            db.refresh(ev)

        comp_result_data = ScoringEngine.compare_ideas(ideas, created_evals, weights_dict)
        comp = ComparisonResult(
            project_id=project.id,
            configured_weights=weights_dict,
            recommended_idea_id=comp_result_data.get("recommended_idea_id"),
            recommendation_rationale=comp_result_data.get("recommendation_rationale", ""),
            tradeoff_analysis=comp_result_data.get("tradeoff_analysis", {}),
            is_tie=comp_result_data.get("is_tie", 0),
            created_at=datetime.now(timezone.utc)
        )
        db.add(comp)
        db.commit()
        db.refresh(comp)
        evals = created_evals

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

    # Recalculate and persist updated composite score on each evaluation
    for ev in evals:
        ev.overall_score = ScoringEngine.calculate_overall_score(ev.dimension_scores, weights_dict)
    db.commit()

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
