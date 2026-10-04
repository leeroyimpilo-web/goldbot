from app.economic_calendar import current_news_gate


def test_calendar_failure_is_non_blocking_in_research(monkeypatch):
    import app.economic_calendar as calendar
    monkeypatch.setattr(calendar.settings, "trading_mode", "research")
    monkeypatch.setattr(calendar, "nearby_events", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("db")))
    result = current_news_gate()
    assert result.blocked is False
    assert "research_only" in result.reason


def test_calendar_failure_blocks_demo(monkeypatch):
    import app.economic_calendar as calendar
    monkeypatch.setattr(calendar.settings, "trading_mode", "demo")
    monkeypatch.setattr(calendar, "nearby_events", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("db")))
    result = current_news_gate()
    assert result.blocked is True
