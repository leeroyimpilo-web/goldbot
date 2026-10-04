from __future__ import annotations

import pandas as pd

from app.backtest import run_mtf_breakout_backtest


PERIODS = {
    "development": ("2015-01-01", "2022-01-01"),
    "validation": ("2022-01-01", "2024-01-01"),
    "oos": ("2024-01-01", "2026-01-01"),
    "holdout_2026": ("2026-01-01", "2027-01-01"),
}


def _slice(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    return frame[(frame["time"] >= start_ts) & (frame["time"] < end_ts)].copy()


def chronological_evaluation(
    h1: pd.DataFrame,
    m15: pd.DataFrame,
    *,
    parameters: dict | None = None,
    normal_cost_r: float = 0.05,
    stress_cost_r: float = 0.10,
) -> dict:
    parameters = parameters or {}
    results: dict[str, dict] = {}

    for name, (start, end) in PERIODS.items():
        h = _slice(h1, start, end)
        m = _slice(m15, start, end)
        if len(h) < 220 or len(m) < 60:
            results[name] = {
                "available": False,
                "reason": "insufficient_data",
                "h1_bars": len(h),
                "m15_bars": len(m),
            }
            continue

        normal = run_mtf_breakout_backtest(
            h,
            m,
            round_trip_cost_r=normal_cost_r,
            **parameters,
        )
        stress = run_mtf_breakout_backtest(
            h,
            m,
            round_trip_cost_r=stress_cost_r,
            **parameters,
        )
        results[name] = {
            "available": True,
            "normal": normal["metrics"],
            "stress": stress["metrics"],
            "start": start,
            "end": end,
        }

    return {
        "periods": results,
        "normal_cost_r": normal_cost_r,
        "stress_cost_r": stress_cost_r,
        "warning": "The 2026 holdout should only be inspected after strategy and parameters are frozen.",
    }
