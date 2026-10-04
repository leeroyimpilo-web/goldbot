from __future__ import annotations

from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class PerformanceMetrics:
    trades: int
    wins: int
    losses: int
    win_rate: float
    net_r: float
    expectancy_r: float
    profit_factor: float | None
    max_drawdown_r: float

    def to_dict(self) -> dict:
        return asdict(self)


def performance_metrics(r_multiples: list[float]) -> PerformanceMetrics:
    if not r_multiples:
        return PerformanceMetrics(0, 0, 0, 0.0, 0.0, 0.0, None, 0.0)

    wins = [r for r in r_multiples if r > 0]
    losses = [r for r in r_multiples if r < 0]
    gross_profit = sum(wins)
    gross_loss = abs(sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else None

    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in r_multiples:
        equity += r
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    return PerformanceMetrics(
        trades=len(r_multiples),
        wins=len(wins),
        losses=len(losses),
        win_rate=len(wins) / len(r_multiples),
        net_r=sum(r_multiples),
        expectancy_r=sum(r_multiples) / len(r_multiples),
        profit_factor=profit_factor if profit_factor is None or math.isfinite(profit_factor) else None,
        max_drawdown_r=max_dd,
    )
