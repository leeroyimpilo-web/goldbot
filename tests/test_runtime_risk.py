from datetime import datetime, timezone

from app.runtime_risk import update_runtime_risk


def test_runtime_risk_tracks_peak_and_daily_loss():
    state = {}
    now = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)
    a = update_runtime_risk(state, equity=100000, now=now)
    assert a.daily_return == 0
    b = update_runtime_risk(state, equity=99000, now=now)
    assert round(b.daily_return, 4) == -0.01
    assert round(b.drawdown, 4) == 0.01


def test_new_day_resets_daily_start_but_not_peak():
    state = {}
    d1 = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)
    d2 = datetime(2026, 10, 5, 12, 0, tzinfo=timezone.utc)
    update_runtime_risk(state, equity=100000, now=d1)
    m = update_runtime_risk(state, equity=99000, now=d2)
    assert m.daily_return == 0
    assert m.equity_peak == 100000
