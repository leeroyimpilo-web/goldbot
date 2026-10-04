from app.risk import RiskDecision
from app.strategy import StrategySignal
from app.trade_planner import build_trade_plan


def test_buy_trade_plan_uses_equity_risk_and_18r_target():
    plan = build_trade_plan(
        signal=StrategySignal("buy", "test", 3000.0, 10.0),
        strategy_version="test_v1",
        executable_entry=3010.0,
        equity=100_000.0,
        risk=RiskDecision(True, "ok", 0.0025),
        loss_per_lot=500.0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
    )
    assert round(plan.risk_cash, 2) == 250.0
    assert plan.volume == 0.5
    assert round((plan.target - plan.entry) / (plan.entry - plan.stop), 6) == 1.8
