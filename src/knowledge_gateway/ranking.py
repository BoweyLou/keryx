from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RankingWeights:
    freshness_weight: float = 0.15
    project_weight: float = 0.25
    semantic_weight: float = 0.45
    lexical_weight: float = 0.40
    pinned_bonus: float = 0.15


def blend_scores(
    *,
    lexical_score: float,
    semantic_score: float,
    freshness_score: float,
    project_match: float,
    note_type_weight: float,
    pinned: bool,
    weights: RankingWeights,
) -> float:
    base = (
        lexical_score * weights.lexical_weight
        + semantic_score * weights.semantic_weight
        + freshness_score * weights.freshness_weight
        + project_match * weights.project_weight
    )
    if pinned:
        base += weights.pinned_bonus
    return round(base * note_type_weight, 6)

