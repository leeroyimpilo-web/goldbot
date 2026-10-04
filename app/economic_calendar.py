from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.config import settings
from app.database import EconomicEventRecord, SessionLocal
from app.news import EconomicEvent, NewsGateResult, evaluate_news_gate


def add_event(
    *,
    name: str,
    scheduled_at: datetime,
    impact: str = "high",
    currency: str = "USD",
    source: str | None = None,
    external_id: str | None = None,
) -> int:
    if scheduled_at.tzinfo is None:
        raise ValueError("scheduled_at must be timezone-aware")

    with SessionLocal() as session:
        row = EconomicEventRecord(
            name=name,
            scheduled_at=scheduled_at,
            impact=impact,
            currency=currency,
            source=source,
            external_id=external_id,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def nearby_events(
    *,
    now: datetime | None = None,
    hours_before: int = 2,
    hours_after: int = 2,
) -> list[EconomicEvent]:
    now = now or datetime.now(timezone.utc)
    start = now - timedelta(hours=hours_before)
    end = now + timedelta(hours=hours_after)

    with SessionLocal() as session:
        rows = session.scalars(
            select(EconomicEventRecord)
            .where(EconomicEventRecord.scheduled_at >= start)
            .where(EconomicEventRecord.scheduled_at <= end)
            .order_by(EconomicEventRecord.scheduled_at)
        ).all()

        return [
            EconomicEvent(
                name=row.name,
                scheduled_at=row.scheduled_at,
                impact=row.impact,
                currency=row.currency,
            )
            for row in rows
        ]


def current_news_gate(now: datetime | None = None) -> NewsGateResult:
    try:
        return evaluate_news_gate(nearby_events(now=now), now=now)
    except Exception as exc:
        # Fail closed outside pure research mode. A missing/failed calendar must
        # never silently permit demo/live entries.
        if settings.trading_mode.lower() in {"demo", "live"}:
            return NewsGateResult(
                blocked=True,
                event_name=None,
                minutes_to_event=None,
                reason=f"economic_calendar_unavailable:{type(exc).__name__}",
            )
        return NewsGateResult(
            blocked=False,
            event_name=None,
            minutes_to_event=None,
            reason=f"economic_calendar_unavailable_research_only:{type(exc).__name__}",
        )
