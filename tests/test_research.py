from app.research import research_score


def test_research_score_rejects_tiny_samples():
    score = research_score(
        {
            "trades": 5,
            "expectancy_r": 1.0,
            "max_drawdown_r": 0.2,
            "profit_factor": 10.0,
        }
    )
    assert score == -999.0


def test_research_score_rewards_positive_quality():
    good = research_score(
        {
            "trades": 100,
            "expectancy_r": 0.1,
            "max_drawdown_r": 3.0,
            "profit_factor": 1.4,
        }
    )
    bad = research_score(
        {
            "trades": 100,
            "expectancy_r": -0.1,
            "max_drawdown_r": 8.0,
            "profit_factor": 0.8,
        }
    )
    assert good > bad
