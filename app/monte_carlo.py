from __future__ import annotations

from dataclasses import asdict, dataclass
import numpy as np


@dataclass(frozen=True)
class MonteCarloSummary:
    paths: int
    trades_per_path: int
    median_return_r: float
    p05_return_r: float
    p95_return_r: float
    median_max_drawdown_r: float
    p95_max_drawdown_r: float
    p99_max_drawdown_r: float

    def to_dict(self) -> dict:
        return asdict(self)


def _max_drawdown(path: np.ndarray) -> float:
    curve = np.cumsum(path)
    peaks = np.maximum.accumulate(np.concatenate(([0.0], curve)))[:-1]
    drawdowns = peaks - curve
    return float(max(0.0, drawdowns.max(initial=0.0)))


def bootstrap_monte_carlo(
    trade_returns_r: list[float],
    *,
    paths: int = 10000,
    trades_per_path: int | None = None,
    seed: int = 42,
) -> MonteCarloSummary:
    if len(trade_returns_r) < 20:
        raise ValueError("At least 20 historical trade returns are required")
    if paths < 100:
        raise ValueError("At least 100 Monte Carlo paths are required")

    values = np.asarray(trade_returns_r, dtype=float)
    n = trades_per_path or len(values)
    if n <= 0:
        raise ValueError("trades_per_path must be positive")

    rng = np.random.default_rng(seed)
    sampled = rng.choice(values, size=(paths, n), replace=True)
    returns = sampled.sum(axis=1)
    drawdowns = np.asarray([_max_drawdown(row) for row in sampled], dtype=float)

    return MonteCarloSummary(
        paths=paths,
        trades_per_path=n,
        median_return_r=float(np.median(returns)),
        p05_return_r=float(np.percentile(returns, 5)),
        p95_return_r=float(np.percentile(returns, 95)),
        median_max_drawdown_r=float(np.median(drawdowns)),
        p95_max_drawdown_r=float(np.percentile(drawdowns, 95)),
        p99_max_drawdown_r=float(np.percentile(drawdowns, 99)),
    )
