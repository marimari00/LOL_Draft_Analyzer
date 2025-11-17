import pytest

from backend import draft_api


def _rec(name, score, archetype, role=None):
    return draft_api.ChampionRecommendation(
        champion=name,
        score=score,
        archetype=archetype,
        recommended_role=role,
        attribute_highlights=[],
        reasoning=["stub"],
        score_breakdown={},
        rationale_tags=[],
    )


def test_family_penalty_promotes_variety():
    ranked = [
        _rec("Jinx", 0.92, "marksman", "BOTTOM"),
        _rec("Aphelios", 0.91, "marksman", "BOTTOM"),
        _rec("Ezreal", 0.9, "marksman", "BOTTOM"),
        _rec("Leona", 0.88, "engage_tank", "UTILITY"),
    ]

    adjusted = draft_api._apply_recommendation_diversity_penalty(ranked)

    assert adjusted[0].champion == "Jinx"
    assert adjusted[1].champion == "Leona"
    ezreal = next(rec for rec in adjusted if rec.champion == "Ezreal")
    assert ezreal.score < 0.88
    assert ezreal.score_breakdown["diversity_penalty"] < 0


def test_role_penalty_discourages_duplicate_lanes():
    ranked = [
        _rec("Lee Sin", 0.86, "diver", "JUNGLE"),
        _rec("Viego", 0.85, "skirmisher", "JUNGLE"),
        _rec("Nidalee", 0.84, "battle_mage", "JUNGLE"),
    ]

    adjusted = draft_api._apply_recommendation_diversity_penalty(ranked)

    first = next(rec for rec in adjusted if rec.champion == "Lee Sin")
    second = next(rec for rec in adjusted if rec.champion == "Viego")
    third = next(rec for rec in adjusted if rec.champion == "Nidalee")

    assert first.score == pytest.approx(0.86)
    assert second.score < 0.85
    assert third.score < second.score
    assert second.score_breakdown["diversity_penalty"] == pytest.approx(-0.035, rel=1e-2)
    assert third.score_breakdown["diversity_penalty"] == pytest.approx(-0.03, rel=1e-2)
