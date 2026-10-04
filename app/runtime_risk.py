from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class RuntimeRiskMetrics:
    daily_return: float
    weekly_return: float
    drawdown: float
    equity_peak: float
    day_start_equity: float
    week_start_equity: float

    def to_dict(self) -> dict:
        return asdict(self)


def update_runtime_risk(
    state: dict,
    *,
    equity: float,
    now: datetime | None = None,
) -> RuntimeRiskMetrics:
    if equity <= 0:
        raise ValueError("Equity must be positive")

    now = now or datetime.now(timezone.utc)
    day_key = now.date().isoformat()
    iso = now.isocalendar()
    week_key = f"{iso.year}-W{iso.week:02d}"

    if state.get("risk_day_key") != day_key:
        state["risk_day_key"] = day_key
        state["day_start_equity"] = equity

    if state.get("risk_week_key") != week_key:
        state["risk_week_key"] = week_key
        state["week_start_equity"] = equity

    peak = max(float(state.get("equity_peak", equity)), equity)
    state["equity_peak"] = peak

    day_start = float(state.get("day_start_equity", equity))
    week_start = float(state.get("week_start_equity", equity))

    daily_return = (equity - day_start) / day_start if day_start > 0 else 0.0
    weekly_return = (equity - week_start) / week_start if week_start > 0 else 0.0
    drawdown = max(0.0, (peak - equity) / peak) if peak > 0 else 0.0

    return RuntimeRiskMetrics(
        daily_return=daily_return,
        weekly_return=weekly_return,
        drawdown=drawdown,
        equity_peak=peak,
        day_start_equity=day_start,
        week_start_equity=week_start,
    )
