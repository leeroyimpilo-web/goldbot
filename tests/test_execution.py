from app.execution import authorize_execution


def test_research_mode_never_executes(monkeypatch):
    from app import execution
    monkeypatch.setattr(execution.settings, "trading_mode", "research")
    result = authorize_execution(broker_trade_mode="demo", strategy_approved=True)
    assert result.allowed is False
    assert result.reason == "research_mode_never_sends_orders"


def test_demo_requires_demo_account(monkeypatch):
    from app import execution
    monkeypatch.setattr(execution.settings, "trading_mode", "demo")
    result = authorize_execution(broker_trade_mode="real", strategy_approved=True)
    assert result.allowed is False


def test_strategy_must_be_approved(monkeypatch):
    from app import execution
    monkeypatch.setattr(execution.settings, "trading_mode", "demo")
    result = authorize_execution(broker_trade_mode="demo", strategy_approved=False)
    assert result.allowed is False
    assert result.reason == "strategy_not_approved"
