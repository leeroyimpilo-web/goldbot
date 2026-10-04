from __future__ import annotations

import numpy as np
import pandas as pd

from app.strategy import MarketSnapshot


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def true_range(frame: pd.DataFrame) -> pd.Series:
    prev_close = frame["close"].shift(1)
    return pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - prev_close).abs(),
            (frame["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    return wilder_smooth(true_range(frame), period)


def adx(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    up_move = frame["high"].diff()
    down_move = -frame["low"].diff()

    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=frame.index,
        dtype=float,
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=frame.index,
        dtype=float,
    )

    atr_values = atr(frame, period).replace(0, np.nan)
    plus_di = 100 * wilder_smooth(plus_dm, period) / atr_values
    minus_di = 100 * wilder_smooth(minus_dm, period) / atr_values
    denominator = (plus_di + minus_di).replace(0, np.nan)
    dx = (100 * (plus_di - minus_di).abs() / denominator).fillna(0.0)
    return wilder_smooth(dx, period)


def donchian_high(frame: pd.DataFrame, period: int = 20) -> pd.Series:
    return frame["high"].shift(1).rolling(period).max()


def donchian_low(frame: pd.DataFrame, period: int = 20) -> pd.Series:
    return frame["low"].shift(1).rolling(period).min()


def build_market_snapshot(h1: pd.DataFrame, m15: pd.DataFrame) -> MarketSnapshot:
    if len(h1) < 220:
        raise ValueError("At least 220 completed H1 bars are required")
    if len(m15) < 40:
        raise ValueError("At least 40 completed M15 bars are required")

    h1 = h1.copy()
    m15 = m15.copy()

    h1["ema200"] = ema(h1["close"], 200)
    h1["ema50"] = ema(h1["close"], 50)

    m15["atr14"] = atr(m15, 14)
    m15["adx14"] = adx(m15, 14)
    m15["donchian_high20"] = donchian_high(m15, 20)
    m15["donchian_low20"] = donchian_low(m15, 20)

    h = h1.iloc[-1]
    h_old = h1.iloc[-7]
    m = m15.iloc[-1]

    required = [
        h["ema200"],
        h["ema50"],
        h_old["ema50"],
        m["atr14"],
        m["adx14"],
        m["donchian_high20"],
        m["donchian_low20"],
    ]
    if any(pd.isna(v) for v in required):
        raise ValueError("Indicator warm-up incomplete")

    return MarketSnapshot(
        h1_close=float(h["close"]),
        h1_ema200=float(h["ema200"]),
        h1_ema50=float(h["ema50"]),
        h1_ema50_six_bars_ago=float(h_old["ema50"]),
        m15_close=float(m["close"]),
        m15_atr14=float(m["atr14"]),
        m15_adx14=float(m["adx14"]),
        donchian_high20=float(m["donchian_high20"]),
        donchian_low20=float(m["donchian_low20"]),
    )
