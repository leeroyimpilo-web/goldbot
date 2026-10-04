import numpy as np
import pandas as pd

from app.validation import chronological_evaluation


def make_bars(start: str, count: int, freq: str, step: float) -> pd.DataFrame:
    close = 2000 + np.arange(count) * step
    return pd.DataFrame(
        {
            "time": pd.date_range(start, periods=count, freq=freq, tz="UTC"),
            "open": close - 0.1,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "tick_volume": 100,
        }
    )


def test_chronological_evaluation_marks_missing_periods():
    h1 = make_bars("2026-01-01", 500, "h", 0.2)
    m15 = make_bars("2026-01-01", 2000, "15min", 0.05)
    result = chronological_evaluation(h1, m15)
    assert result["periods"]["development"]["available"] is False
    assert result["periods"]["holdout_2026"]["available"] is True
