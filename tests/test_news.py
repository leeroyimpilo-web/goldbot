from datetime import datetime, timezone

from app.news import EconomicEvent, evaluate_news_gate


def test_fomc_blackout_blocks():
    now = datetime(2026, 10, 4, 18, 0, tzinfo=timezone.utc)
    event = EconomicEvent(
        name="FOMC Rate Decision",
        scheduled_at=datetime(2026, 10, 4, 18, 30, tzinfo=timezone.utc),
    )
    gate = evaluate_news_gate([event], now=now)
    assert gate.blocked is True
    assert gate.event_name == "FOMC Rate Decision"


def test_far_event_does_not_block():
    now = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)
    event = EconomicEvent(
        name="CPI",
        scheduled_at=datetime(2026, 10, 4, 18, 30, tzinfo=timezone.utc),
    )
    assert evaluate_news_gate([event], now=now).blocked is False
