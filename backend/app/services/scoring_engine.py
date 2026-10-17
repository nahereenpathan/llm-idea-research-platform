from typing import List, Dict, Any, Optional
from app.models.idea import Idea
from app.models.evaluation import Evaluation


class ScoringEngine:
    """
    Transparent, explainable multi-criteria scoring and comparison engine.
    Calculates weighted composite scores across 10 explicit dimensions,
    provides trade-off analysis, treats cost and complexity inversely,
    and detects ties, uncertainties, and evidence gaps.
    """

    TIE_THRESHOLD = 2.0  # Points on a 100-point scale
    INSUFFICIENT_EVIDENCE_THRESHOLD = 4.5  # Points on a 1-10 scale

    # Dimensions where a higher raw rating indicates higher friction, hurdle, or cost
    INVERTED_DIMENSIONS = {
        "implementation_complexity",
        "estimated_development_cost"
    }

    DIMENSION_METADATA = {
        "problem_significance": {
            "name": "Problem Significance",
            "type": "beneficial",
            "description": "Urgency and economic/human magnitude of the pain point."
        },
        "target_user_clarity": {
            "name": "Target-User Clarity",
            "type": "beneficial",
            "description": "Specificity of buyer persona, daily workflow, and purchase authority."
        },
        "technical_feasibility": {
            "name": "Technical Feasibility",
            "type": "beneficial",
            "description": "Achievability using existing technology, APIs, and algorithms without fundamental R&D breakthroughs."
        },
        "implementation_complexity": {
            "name": "Implementation Simplicity (Inverse Complexity)",
            "type": "frictional",
            "description": "Raw rating measures architectural friction. Inverted in scoring so lower complexity yields higher feasibility."
        },
        "estimated_development_cost": {
            "name": "Capital Efficiency (Inverse Cost)",
            "type": "frictional",
            "description": "Raw rating measures budget requirements. Inverted in scoring so lower development cost yields higher capital efficiency."
        },
        "adoption_potential": {
            "name": "Adoption & Validation Potential",
            "type": "beneficial",
            "description": "Ease of onboarding, willingness to try, and alignment with user incentives."
        },
        "competitive_landscape": {
            "name": "Competitive Differentiation",
            "type": "beneficial",
            "description": "Defensibility against incumbent solutions and substitutable alternatives."
        },
        "novelty": {
            "name": "Novelty & Prior-Work Distance",
            "type": "beneficial",
            "description": "Degree of divergence from prior published literature and commercial products."
        },
        "security_privacy_ethics": {
            "name": "Security, Privacy & Ethics",
            "type": "beneficial",
            "description": "Manageability of regulatory compliance (GDPR, HIPAA), security attack surfaces, and ethical alignment."
        },
        "evidence_quality": {
            "name": "Evidence Quality & Confidence",
            "type": "beneficial",
            "description": "Level of factual backing from user discovery, verified citations, or benchmarks vs speculative assumption."
        }
    }

    @classmethod
    def get_effective_dimension_score(cls, dim: str, raw_score: float) -> float:
        """
        Converts a raw 1.0-10.0 assessment to an effective performance contribution.
        - For beneficial dimensions, effective_score = raw_score (higher is better).
        - For frictional dimensions (complexity and development cost), raw rating
          represents friction or capital intensity (10 = maximum complexity/cost).
          It is inverted: effective_score = 11.0 - raw_score (e.g. raw 2 -> effective 9.0;
          raw 9 -> effective 2.0).
        """
        raw = max(1.0, min(10.0, float(raw_score)))
        if dim in cls.INVERTED_DIMENSIONS:
            return round(11.0 - raw, 2)
        return round(raw, 2)

    @classmethod
    def calculate_overall_score(cls, scores: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
        """
        Computes composite weighted score scaled from 0 to 100.
        Score = (Sum(w_i * S_eff,i) / Sum(w_i)) * 10
        Where S_eff,i is the effective 1-10 performance rating (with cost/complexity inverted).
        """
        default_weight = 1.0
        total_weighted_points = 0.0
        total_weights = 0.0

        for dim, raw_score in scores.items():
            eff_score = cls.get_effective_dimension_score(dim, raw_score)
            w = weights.get(dim, default_weight) if weights else default_weight
            w = max(0.0, float(w))
            total_weighted_points += eff_score * w
            total_weights += w

        if total_weights <= 0:
            return 0.0

        composite = (total_weighted_points / total_weights) * 10.0
        return round(composite, 2)

    @classmethod
    def get_scoring_breakdown(
        cls,
        scores: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Returns a transparent mathematical breakdown of how the composite score
        was derived from raw scores, effective transformations, and priority weights.
        """
        default_weight = 1.0
        total_weights = sum(max(0.0, float(weights.get(d, default_weight) if weights else default_weight)) for d in scores)
        breakdown_items = []

        for dim, raw_val in scores.items():
            raw = max(1.0, min(10.0, float(raw_val)))
            eff = cls.get_effective_dimension_score(dim, raw)
            w = max(0.0, float(weights.get(dim, default_weight) if weights else default_weight))
            normalized_weight = round((w / total_weights) * 100, 1) if total_weights > 0 else 0.0
            point_contrib = round((eff * w / total_weights) * 10.0, 2) if total_weights > 0 else 0.0

            meta = cls.DIMENSION_METADATA.get(dim, {"name": dim.replace("_", " ").title(), "type": "beneficial"})
            breakdown_items.append({
                "dimension": dim,
                "name": meta["name"],
                "type": meta["type"],
                "raw_score": raw,
                "effective_score": eff,
                "weight": w,
                "normalized_weight_pct": normalized_weight,
                "point_contribution": point_contrib,
                "is_inverted": dim in cls.INVERTED_DIMENSIONS
            })

        composite = cls.calculate_overall_score(scores, weights)
        formula = (
            "Composite Score = [Sum(w_i * S_eff,i) / Sum(w_i)] * 10\n"
            "• S_eff,i: Effective score (1-10). Positive dimensions contribute directly. "
            "Implementation complexity and development cost are inverted (11.0 - raw_score) "
            "so that higher complexity or cost does not artificially inflate the score.\n"
            "• Output normalized to 0–100 scale."
        )

        return {
            "composite_score": composite,
            "dimensions": breakdown_items,
            "formula_explanation": formula,
            "total_weights_sum": round(total_weights, 2)
        }

    @classmethod
    def compare_ideas(
        cls,
        ideas: List[Idea],
        evaluations: List[Evaluation],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Compares evaluated ideas using the specified weights, computes rank order,
        checks for ties/uncertainty and insufficient evidence, and crafts transparent rationale.
        """
        if not ideas or not evaluations:
            return {
                "recommended_idea_id": None,
                "recommendation_rationale": "Insufficient data to perform comparative ranking.",
                "tradeoff_analysis": {},
                "is_tie": 1
            }

        eval_map = {e.idea_id: e for e in evaluations}
        ranked_list = []

        for idea in ideas:
            ev = eval_map.get(idea.id)
            if not ev:
                continue
            dim_scores = ev.dimension_scores
            composite = cls.calculate_overall_score(dim_scores, weights)
            breakdown = cls.get_scoring_breakdown(dim_scores, weights)

            ranked_list.append({
                "idea_id": idea.id,
                "title": idea.title,
                "composite_score": composite,
                "dimension_scores": dim_scores,
                "effective_scores": {d["dimension"]: d["effective_score"] for d in breakdown["dimensions"]},
                "evidence_quality": dim_scores.get("evidence_quality", 7.0),
                "strengths": ev.strengths,
                "weaknesses": ev.weaknesses,
                "risks": ev.risks,
                "assumptions": getattr(ev, "assumptions", []) or [],
                "missing_information": ev.missing_information,
                "recommended_experiments": ev.recommended_experiments
            })

        # Sort descending by composite score
        ranked_list.sort(key=lambda x: x["composite_score"], reverse=True)

        if not ranked_list:
            return {
                "recommended_idea_id": None,
                "recommendation_rationale": "No evaluations found for comparison.",
                "tradeoff_analysis": {},
                "is_tie": 1
            }

        # Check for pervasive insufficient evidence across all candidates
        avg_evidence = sum(item["evidence_quality"] for item in ranked_list) / len(ranked_list)
        low_evidence_flag = (avg_evidence < cls.INSUFFICIENT_EVIDENCE_THRESHOLD)

        # Single idea evaluation
        if len(ranked_list) == 1:
            top = ranked_list[0]
            evidence_note = (
                " Note: Evidence quality is currently low (< 4.5/10); treat these ratings as exploratory hypotheses."
                if low_evidence_flag else ""
            )
            return {
                "recommended_idea_id": top["idea_id"],
                "recommendation_rationale": (
                    f"'{top['title']}' is the sole candidate evaluated in this project, scoring {top['composite_score']}/100. "
                    f"Ratings reflect feasibility and validation potential based on submitted parameters.{evidence_note}"
                ),
                "tradeoff_analysis": {
                    "rankings": ranked_list,
                    "evidence_confidence": "Low / Unverified" if low_evidence_flag else "Moderate Heuristic",
                    "disclaimer": "Ratings are heuristic diligence estimates designed to guide experiments, not guarantees of commercial outcome."
                },
                "is_tie": 1 if low_evidence_flag else 0
            }

        top = ranked_list[0]
        runner_up = ranked_list[1]
        score_diff = round(top["composite_score"] - runner_up["composite_score"], 2)

        # Dimension contrast analysis between top two candidates
        top_advantages = []
        runner_advantages = []
        for dim, top_raw in top["dimension_scores"].items():
            top_eff = top["effective_scores"].get(dim, top_raw)
            run_eff = runner_up["effective_scores"].get(dim, runner_up["dimension_scores"].get(dim, 7.0))
            diff = top_eff - run_eff
            name = cls.DIMENSION_METADATA.get(dim, {}).get("name", dim.replace("_", " ").title())
            if diff >= 1.0:
                top_advantages.append(f"{name} (+{diff:.1f})")
            elif diff <= -1.0:
                runner_advantages.append(f"{name} (+{abs(diff):.1f})")

        # Case 1: Low Evidence Quality / Inconclusive
        if low_evidence_flag:
            rationale = (
                f"Inconclusive Recommendation due to Low Evidence Baseline: Both '{top['title']}' ({top['composite_score']}/100) "
                f"and '{runner_up['title']}' ({runner_up['composite_score']}/100) have low empirical evidence quality (< {cls.INSUFFICIENT_EVIDENCE_THRESHOLD}/10). "
                "Current ratings are model-assisted heuristic projections rather than verified findings. "
                "Recommended Action: Execute the initial validation experiments before making capital allocation commitments."
            )
            return {
                "recommended_idea_id": top["idea_id"],
                "recommendation_rationale": rationale,
                "tradeoff_analysis": {
                    "rankings": ranked_list,
                    "score_difference": score_diff,
                    "is_inconclusive": True,
                    "top_advantages": top_advantages[:3],
                    "runner_up_advantages": runner_advantages[:3],
                    "disclaimer": "Ratings are model-assisted diligence estimates, not objective probability of success."
                },
                "is_tie": 1
            }

        # Case 2: Statistical Parity / Tie (Score difference < TIE_THRESHOLD)
        if score_diff < cls.TIE_THRESHOLD:
            top_str = ", ".join(top_advantages[:2]) if top_advantages else "balanced overall execution"
            run_str = ", ".join(runner_advantages[:2]) if runner_advantages else "competitive feasibility"
            rationale = (
                f"Statistical Parity / Close Decision between '{top['title']}' ({top['composite_score']}/100) "
                f"and '{runner_up['title']}' ({runner_up['composite_score']}/100) (Margin: {score_diff} pts). "
                f"'{top['title']}' holds advantages in: {top_str}. "
                f"Conversely, '{runner_up['title']}' leads in: {run_str}. "
                "Recommendation: Decision should be guided by your team's immediate risk posture (e.g. speed vs differentiation)."
            )
            return {
                "recommended_idea_id": top["idea_id"],
                "recommendation_rationale": rationale,
                "tradeoff_analysis": {
                    "rankings": ranked_list,
                    "score_difference": score_diff,
                    "is_tie": True,
                    "top_advantages": top_advantages[:3],
                    "runner_up_advantages": runner_advantages[:3],
                    "disclaimer": "Ratings are model-assisted diligence estimates, not objective probability of success."
                },
                "is_tie": 1
            }

        # Case 3: Decisive or Moderate Winner
        margin_label = "Decisive" if score_diff >= 6.0 else "Moderate"
        top_str = ", ".join(top_advantages[:3]) if top_advantages else "higher combined dimensional strength"
        runner_str = (
            f" However, '{runner_up['title']}' demonstrates superior performance in {', '.join(runner_advantages[:2])}."
            if runner_advantages else ""
        )
        rationale = (
            f"'{top['title']}' is recommended as the leading candidate with a composite score of {top['composite_score']}/100 "
            f"({margin_label} margin of +{score_diff} points over '{runner_up['title']}' under current priority weights). "
            f"Key driving advantages: {top_str}.{runner_str}"
        )

        return {
            "recommended_idea_id": top["idea_id"],
            "recommendation_rationale": rationale,
            "tradeoff_analysis": {
                "rankings": ranked_list,
                "score_difference": score_diff,
                "margin_of_victory": margin_label,
                "top_advantages": top_advantages[:3],
                "runner_up_advantages": runner_advantages[:3],
                "disclaimer": "Ratings are model-assisted diligence estimates, not objective probability of success."
            },
            "is_tie": 0
        }
