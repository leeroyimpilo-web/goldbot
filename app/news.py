from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class EconomicEvent:
    name: str
    scheduled_at: datetime
    impact: str = "high"
    currency: str = "USD"


@dataclass(frozen=True)
class NewsGateResult:
    blocked: bool
    event_name: str | None
    minutes_to_event: float | None
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


DEFAULT_WINDOWS = {
    "NFP": (30, 15),
    "CPI": (30, 15),
    "CORE CPI": (30, 15),
    "PCE": (30, 15),
    "GDP": (30, 15),
    "PPI": (20, 15),
    "RETAIL SALES": (20, 15),
    "FOMC": (60, 30),
}


def _window_for(name: str) -> tuple[int, int]:
    upper = name.upper()
    for key, window in DEFAULT_WINDOWS.items():
        if key in upper:
            return window
    return (15, 10)


def evaluate_news_gate(
    events: list[EconomicEvent],
    *,
    now: datetime | None = None,
) -> NewsGateResult:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    relevant = [
        e for e in events
        if e.currency.upper() == "USD"
        and e.impact.lower() == "high"
    ]

    for event in sorted(relevant, key=lambda e: e.scheduled_at):
        before_min, after_min = _window_for(event.name)
        start = event.scheduled_at - timedelta(minutes=before_min)
        end = event.scheduled_at + timedelta(minutes=after_min)
        if start <= now <= end:
            minutes_to = (event.scheduled_at - now).total_seconds() / 60.0
            return NewsGateResult(
                blocked=True,
                event_name=event.name,
                minutes_to_event=minutes_to,
                reason="high_impact_usd_event_blackout",
            )

    return NewsGateResult(
        blocked=False,
        event_name=None,
        minutes_to_event=None,
        reason="no_news_blackout",
    )
