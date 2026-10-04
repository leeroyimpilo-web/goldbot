from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import product

import pandas as pd

from app.backtest import run_mtf_breakout_backtest


@dataclass(frozen=True)
class CandidateResult:
    parameters: dict
    metrics: dict
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


def research_score(metrics: dict) -> float:
    trades = int(metrics.get("trades", 0))
    expectancy = float(metrics.get("expectancy_r", 0.0))
    max_dd = float(metrics.get("max_drawdown_r", 0.0))
    pf = metrics.get("profit_factor")
    pf_value = float(pf) if pf is not None else 0.0

    if trades < 20:
        return -999.0

    # Reward net quality while penalizing fragile high drawdown.
    return expectancy * 100.0 + min(pf_value, 3.0) * 10.0 - max_dd


def parameter_grid_search(
    h1: pd.DataFrame,
    m15: pd.DataFrame,
    *,
    adx_values: tuple[float, ...] = (18.0, 20.0, 22.0, 25.0, 28.0),
    stop_atr_values: tuple[float, ...] = (1.0, 1.2, 1.4, 1.6),
    target_r_values: tuple[float, ...] = (1.5, 1.8, 2.0, 2.5),
    breakout_buffers: tuple[float, ...] = (0.0, 0.05, 0.10),
    cost_r: float = 0.05,
    top_n: int = 20,
) -> dict:
    candidates: list[CandidateResult] = []

    for adx_threshold, stop_atr, target_r, buffer in product(
        adx_values,
        stop_atr_values,
        target_r_values,
        breakout_buffers,
    ):
        result = run_mtf_breakout_backtest(
            h1,
            m15,
            adx_threshold=adx_threshold,
            stop_atr=stop_atr,
            target_r=target_r,
            breakout_buffer_atr=buffer,
            round_trip_cost_r=cost_r,
        )
        metrics = result["metrics"]
        params = {
            "adx_threshold": adx_threshold,
            "stop_atr": stop_atr,
            "target_r": target_r,
            "breakout_buffer_atr": buffer,
            "cost_r": cost_r,
        }
        candidates.append(
            CandidateResult(
                parameters=params,
                metrics=metrics,
                score=research_score(metrics),
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    survivors = [
        c
        for c in candidates
        if c.metrics["trades"] >= 20
        and c.metrics["expectancy_r"] > 0
        and (c.metrics["profit_factor"] or 0) > 1.0
    ]

    return {
        "tested": len(candidates),
        "survivors": len(survivors),
        "top": [c.to_dict() for c in candidates[:top_n]],
        "warning": "Grid results are research candidates, not proof of future profitability.",
    }
