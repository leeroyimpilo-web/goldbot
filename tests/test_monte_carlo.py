from app.monte_carlo import bootstrap_monte_carlo


def test_monte_carlo_is_reproducible():
    trades = [1.5, -1.0] * 20
    a = bootstrap_monte_carlo(trades, paths=500, seed=7)
    b = bootstrap_monte_carlo(trades, paths=500, seed=7)
    assert a == b
    assert a.p99_max_drawdown_r >= a.median_max_drawdown_r
