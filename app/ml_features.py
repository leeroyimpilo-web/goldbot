from __future__ import annotations

import numpy as np
import pandas as pd

from app.indicators import adx, atr, ema


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).fillna(50.0)


def current_meta_features(
    h1: pd.DataFrame,
    m15: pd.DataFrame,
    *,
    spread_percentile: float,
    news_proximity_minutes: float = 999.0,
) -> dict:
    if len(h1) < 220 or len(m15) < 100:
        raise ValueError("Insufficient bars for meta features")

    h = h1.copy()
    m = m15.copy()

    h["atr14"] = atr(h, 14)
    h["ema50"] = ema(h["close"], 50)
    m["atr14"] = atr(m, 14)
    m["adx14"] = adx(m, 14)
    m["rsi14"] = rsi(m["close"], 14)

    basis = m["close"].rolling(20).mean()
    std = m["close"].rolling(20).std(ddof=0)
    m["bb_width"] = ((basis + 2 * std) - (basis - 2 * std)) / basis.replace(0, np.nan)

    typical = (m["high"] + m["low"] + m["close"]) / 3.0
    weights = m.get("tick_volume", pd.Series(1.0, index=m.index)).replace(0, 1)
    cumulative_weight = weights.cumsum()
    vwap = (typical * weights).cumsum() / cumulative_weight

    atr_h = float(h["atr14"].iloc[-1])
    atr_m = float(m["atr14"].iloc[-1])
    if atr_h <= 0 or atr_m <= 0:
        raise ValueError("ATR must be positive")

    atr_window = m["atr14"].dropna().tail(500)
    atr_percentile = float((atr_window <= atr_m).mean() * 100.0)
    ema_slope_atr = float((h["ema50"].iloc[-1] - h["ema50"].iloc[-7]) / atr_h)
    vwap_distance_atr = float((m["close"].iloc[-1] - vwap.iloc[-1]) / atr_m)
    recent_return = float(m["close"].pct_change(4).iloc[-1])

    time_value = m["time"].iloc[-1] if "time" in m.columns else pd.Timestamp.utcnow()
    hour_utc = float(pd.Timestamp(time_value).hour)

    return {
        "atr_percentile": atr_percentile,
        "adx": float(m["adx14"].iloc[-1]),
        "ema_slope_atr": ema_slope_atr,
        "bb_width": float(m["bb_width"].iloc[-1]),
        "rsi": float(m["rsi14"].iloc[-1]),
        "vwap_distance_atr": vwap_distance_atr,
        "recent_return": recent_return,
        "spread_percentile": float(spread_percentile),
        "hour_utc": hour_utc,
        "news_proximity_minutes": float(news_proximity_minutes),
    }
