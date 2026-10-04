import numpy as np
import pandas as pd

from app.indicators import build_market_snapshot


def make_bars(count: int, start: float, step: float) -> pd.DataFrame:
    close = start + np.arange(count) * step
    return pd.DataFrame(
        {
            "open": close - 0.2,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "tick_volume": 100,
        }
    )


def test_snapshot_builds_after_warmup():
    h1 = make_bars(240, 2000.0, 0.5)
    m15 = make_bars(100, 2100.0, 0.3)
    snapshot = build_market_snapshot(h1, m15)
    assert snapshot.h1_close > snapshot.h1_ema200
    assert snapshot.m15_atr14 > 0
    assert snapshot.donchian_high20 > 0
