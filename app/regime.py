from dataclasses import dataclass

import pandas as pd

from app.indicators import adx, atr, ema


@dataclass(frozen=True)
class RegimeResult:
    name: str
    adx: float
    atr_percentile: float
    slope_score: float
    risk_multiplier: float
    allow_new_entries: bool


def classify_regime(h1: pd.DataFrame) -> RegimeResult:
    if len(h1) < 220:
        raise ValueError("At least 220 H1 bars are required for regime classification")

    frame = h1.copy()
    frame["atr14"] = atr(frame, 14)
    frame["adx14"] = adx(frame, 14)
    frame["ema50"] = ema(frame["close"], 50)

    latest = frame.iloc[-1]
    atr_now = float(latest["atr14"])
    adx_now = float(latest["adx14"])

    if atr_now <= 0:
        raise ValueError("ATR must be positive")

    slope_score = float((frame["ema50"].iloc[-1] - frame["ema50"].iloc[-7]) / atr_now)
    atr_window = frame["atr14"].dropna().tail(500)
    atr_percentile = float((atr_window <= atr_now).mean() * 100.0)

    if atr_percentile >= 97.5:
        return RegimeResult("EXTREME_VOL", adx_now, atr_percentile, slope_score, 0.0, False)
    if atr_percentile >= 90:
        return RegimeResult("HIGH_VOL", adx_now, atr_percentile, slope_score, 0.5, True)
    if adx_now > 25 and abs(slope_score) >= 0.20:
        return RegimeResult("STRONG_TREND", adx_now, atr_percentile, slope_score, 1.0, True)
    if adx_now >= 18:
        return RegimeResult("WEAK_TREND", adx_now, atr_percentile, slope_score, 0.5, True)
    return RegimeResult("RANGE", adx_now, atr_percentile, slope_score, 0.0, False)
