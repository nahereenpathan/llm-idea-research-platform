from typing import List, Dict, Any, Optional, Tuple
from app.schemas.evaluation import DimensionScores, DimensionWeights
from app.models.idea import Idea
from app.models.evaluation import Evaluation


class ScoringEngine:
    """
    Transparent, explainable multi-criteria scoring and comparison engine.
    Calculates weighted composite scores across 10 explicit dimensions,
    provides trade-off analysis, and detects ties/uncertainties.
    """

    TIE_THRESHOLD = 2.0  # Points on a 100-point scale

    @staticmethod
    def calculate_overall_score(scores: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> float:
        """
        Computes composite weighted score scaled from 0 to 100.
        Score = (Sum(w_i * S_i) / Sum(w_i)) * 10
        Each dimension S_i is on a 1 to 10 scale.
        """
        default_weight = 1.0
        total_weighted_points = 0.0
        total_weights = 0.0

        for dim, score in scores.items():
            w = weights.get(dim, default_weight) if weights else default_weight
            # Ensure non-negative weight
            w = max(0.0, float(w))
            total_weighted_points += score * w
            total_weights += w

        if total_weights <= 0:
            return 0.0

        composite = (total_weighted_points / total_weights) * 10.0
        return round(composite, 2)

    @classmethod
    def compare_ideas(
        cls,
        ideas: List[Idea],
        evaluations: List[Evaluation],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Compares evaluated ideas using the specified weights, identifies strengths,
        computes rank order, checks for ties/uncertainty, and crafts transparent rationale.
        """
        if not ideas or not evaluations:
            return {
                "recommended_idea_id": None,
                "recommendation_rationale": "Insufficient data to perform comparative ranking.",
                "tradeoff_analysis": {},
                "is_tie": 1
            }

        # Map evaluation by idea_id
        eval_map = {e.idea_id: e for e in evaluations}
        ranked_list = []

        for idea in ideas:
            ev = eval_map.get(idea.id)
            if not ev:
                continue
            dim_scores = ev.dimension_scores
            composite = cls.calculate_overall_score(dim_scores, weights)
            ranked_list.append({
                "idea_id": idea.id,
                "title": idea.title,
                "composite_score": composite,
                "dimension_scores": dim_scores,
                "strengths": ev.strengths,
                "weaknesses": ev.weaknesses,
                "risks": ev.risks
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

        # If only 1 idea
        if len(ranked_list) == 1:
            top = ranked_list[0]
            return {
                "recommended_idea_id": top["idea_id"],
                "recommendation_rationale": (
                    f"'{top['title']}' is the sole candidate evaluated, scoring {top['composite_score']}/100. "
                    "It presents viable feasibility and structured validation potential."
                ),
                "tradeoff_analysis": {"rankings": ranked_list},
                "is_tie": 0
            }

        top = ranked_list[0]
        runner_up = ranked_list[1]
        score_diff = top["composite_score"] - runner_up["composite_score"]

        # Check for tie / statistical parity
        if score_diff < cls.TIE_THRESHOLD:
            # Tie detected
            top_strengths = ", ".join(top["strengths"][:2]) if top["strengths"] else "solid feasibility"
            runner_strengths = ", ".join(runner_up["strengths"][:2]) if runner_up["strengths"] else "competitive edge"
            rationale = (
                f"Statistical Parity / Close Decision between '{top['title']}' ({top['composite_score']}/100) "
                f"and '{runner_up['title']}' ({runner_up['composite_score']}/100) (Score Difference: {score_diff:.2f} pts). "
                f"'{top['title']}' offers strong advantages in: {top_strengths}. "
                f"However, '{runner_up['title']}' is equally compelling in: {runner_strengths}. "
                "Recommendation: Choose based on whether your immediate priority leans toward faster execution vs higher differentiation."
            )
            return {
                "recommended_idea_id": top["idea_id"],  # Top listed, but flagged as tie
                "recommendation_rationale": rationale,
                "tradeoff_analysis": {
                    "rankings": ranked_list,
                    "score_difference": round(score_diff, 2),
                    "note": "A tie or tight margin was reported. Distinctions should be validated with customer discovery."
                },
                "is_tie": 1
            }

        # Clear winner
        top_dims = sorted(top["dimension_scores"].items(), key=lambda x: x[1], reverse=True)[:3]
        top_dim_names = ", ".join([f"{k.replace('_', ' ').title()} ({v}/10)" for k, v in top_dims])
        rationale = (
            f"'{top['title']}' is recommended as the top candidate with a composite score of {top['composite_score']}/100 "
            f"(outperforming '{runner_up['title']}' by {score_diff:.2f} points under current priority weights). "
            f"Key driving advantages: {top_dim_names}. "
            f"Note that '{runner_up['title']}' remains competitive in specific dimensions such as "
            f"{max(runner_up['dimension_scores'], key=runner_up['dimension_scores'].get).replace('_', ' ').title()}."
        )

        return {
            "recommended_idea_id": top["idea_id"],
            "recommendation_rationale": rationale,
            "tradeoff_analysis": {
                "rankings": ranked_list,
                "score_difference": round(score_diff, 2),
                "margin_of_victory": "Decisive" if score_diff >= 5.0 else "Moderate"
            },
            "is_tie": 0
        }
