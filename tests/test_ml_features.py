import numpy as np
import pandas as pd

from app.ml_features import current_meta_features
from app.ml_meta import FEATURE_COLUMNS


def make_bars(count: int, freq: str, step: float) -> pd.DataFrame:
    close = 2000 + np.arange(count) * step
    return pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=count, freq=freq, tz="UTC"),
            "open": close - 0.1,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "tick_volume": np.arange(count) + 100,
        }
    )


def test_meta_features_match_model_schema():
    features = current_meta_features(
        make_bars(240, "h", 0.4),
        make_bars(1000, "15min", 0.1),
        spread_percentile=50.0,
    )
    assert list(features.keys()) == FEATURE_COLUMNS
