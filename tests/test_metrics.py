from app.metrics import performance_metrics


def test_performance_metrics():
    m = performance_metrics([1.8, -1.0, 0.8, -1.0])
    assert m.trades == 4
    assert m.wins == 2
    assert m.losses == 2
    assert round(m.win_rate, 2) == 0.5
    assert round(m.profit_factor or 0, 2) == 1.3
    assert m.max_drawdown_r >= 1.0
