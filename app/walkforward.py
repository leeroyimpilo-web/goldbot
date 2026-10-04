from __future__ import annotations

import pandas as pd

from app.backtest import run_mtf_breakout_backtest


def _slice(frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return frame[(frame["time"] >= start) & (frame["time"] < end)].copy()


def walk_forward(
    h1: pd.DataFrame,
    m15: pd.DataFrame,
    *,
    train_months: int = 36,
    test_months: int = 6,
    parameters: dict | None = None,
) -> dict:
    parameters = parameters or {}
    h1 = h1.sort_values("time").copy()
    m15 = m15.sort_values("time").copy()

    if h1.empty or m15.empty:
        raise ValueError("Walk-forward requires H1 and M15 data")

    start = max(h1["time"].min(), m15["time"].min())
    end = min(h1["time"].max(), m15["time"].max())

    windows: list[dict] = []
    cursor = pd.Timestamp(start)

    while True:
        train_end = cursor + pd.DateOffset(months=train_months)
        test_end = train_end + pd.DateOffset(months=test_months)
        if test_end > end:
            break

        train_h1 = _slice(h1, cursor, train_end)
        train_m15 = _slice(m15, cursor, train_end)
        test_h1 = _slice(h1, train_end, test_end)
        test_m15 = _slice(m15, train_end, test_end)

        if len(train_h1) >= 220 and len(train_m15) >= 60 and len(test_h1) >= 220 and len(test_m15) >= 60:
            train_result = run_mtf_breakout_backtest(train_h1, train_m15, **parameters)
            test_result = run_mtf_breakout_backtest(test_h1, test_m15, **parameters)
            windows.append(
                {
                    "train_start": str(cursor),
                    "train_end": str(train_end),
                    "test_end": str(test_end),
                    "train_metrics": train_result["metrics"],
                    "test_metrics": test_result["metrics"],
                }
            )

        cursor = cursor + pd.DateOffset(months=test_months)

    profitable = sum(1 for w in windows if w["test_metrics"]["expectancy_r"] > 0)
    return {
        "windows": windows,
        "window_count": len(windows),
        "profitable_test_windows": profitable,
        "profitable_test_ratio": profitable / len(windows) if windows else 0.0,
        "parameters": parameters,
    }
