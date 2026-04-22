from knowledge_gateway.ranking import RankingWeights, blend_scores


def test_blend_scores_prefers_project_match_and_freshness() -> None:
    weights = RankingWeights(freshness_weight=0.15, project_weight=0.25, semantic_weight=0.45, lexical_weight=0.40)

    score = blend_scores(
        lexical_score=0.6,
        semantic_score=0.4,
        freshness_score=1.0,
        project_match=1.0,
        note_type_weight=1.1,
        pinned=False,
        weights=weights,
    )

    weaker_score = blend_scores(
        lexical_score=0.65,
        semantic_score=0.42,
        freshness_score=0.0,
        project_match=0.0,
        note_type_weight=1.0,
        pinned=False,
        weights=weights,
    )

    assert score > weaker_score

