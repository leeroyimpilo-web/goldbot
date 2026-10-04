import numpy as np
import pandas as pd

from app.backtest import run_mtf_breakout_backtest


def bars(count: int, freq: str, step: float) -> pd.DataFrame:
    close = 2000 + np.arange(count) * step
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=count, freq=freq, tz="UTC"),
            "open": close - step / 2,
            "high": close + 2.0,
            "low": close - 2.0,
            "close": close,
            "tick_volume": 100,
        }
    )


def test_backtest_returns_metrics_without_fabricating_results():
    h1 = bars(300, "h", 0.5)
    m15 = bars(1200, "15min", 0.2)
    result = run_mtf_breakout_backtest(h1, m15)
    assert result["strategy"] == "mtf_breakout_v1"
    assert result["assumptions"]["live_claim"] is False
    assert result["metrics"]["trades"] == len(result["trades"])
