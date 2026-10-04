from app.risk import RiskState, evaluate_risk


def test_normal_state_is_allowed():
    result = evaluate_risk(RiskState(equity=100_000, daily_return=0.0, weekly_return=0.0, drawdown=0.0))
    assert result.allowed is True


def test_daily_loss_blocks_trading():
    result = evaluate_risk(RiskState(equity=100_000, daily_return=-0.01, weekly_return=-0.01, drawdown=0.01))
    assert result.allowed is False
    assert result.reason == "daily_loss_limit"


def test_hard_drawdown_kills_new_trades():
    result = evaluate_risk(RiskState(equity=90_000, daily_return=0.0, weekly_return=0.0, drawdown=0.10))
    assert result.allowed is False
    assert result.reason == "hard_drawdown_kill_switch"
