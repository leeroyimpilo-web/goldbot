from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from app.indicators import adx, atr, donchian_high, donchian_low, ema
from app.metrics import performance_metrics


@dataclass(frozen=True)
class BacktestTrade:
    side: str
    entry_time: str
    exit_time: str
    entry: float
    stop: float
    target: float
    exit: float
    gross_r: float
    cost_r: float
    net_r: float
    exit_reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def _prepare(h1: pd.DataFrame, m15: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    h1 = h1.copy().sort_values("time").reset_index(drop=True)
    m15 = m15.copy().sort_values("time").reset_index(drop=True)

    h1["ema200"] = ema(h1["close"], 200)
    h1["ema50"] = ema(h1["close"], 50)
    h1["ema50_lag6"] = h1["ema50"].shift(6)

    m15["atr14"] = atr(m15, 14)
    m15["adx14"] = adx(m15, 14)
    m15["donchian_high20"] = donchian_high(m15, 20)
    m15["donchian_low20"] = donchian_low(m15, 20)
    return h1, m15


def run_mtf_breakout_backtest(
    h1: pd.DataFrame,
    m15: pd.DataFrame,
    *,
    adx_threshold: float = 22.0,
    breakout_buffer_atr: float = 0.05,
    stop_atr: float = 1.2,
    target_r: float = 1.8,
    max_holding_bars: int = 12,
    round_trip_cost_r: float = 0.05,
) -> dict:
    if len(h1) < 220 or len(m15) < 60:
        raise ValueError("Insufficient data for MTF backtest")

    h1, m15 = _prepare(h1, m15)
    merged = pd.merge_asof(
        m15,
        h1[["time", "close", "ema200", "ema50", "ema50_lag6"]].rename(
            columns={
                "close": "h1_close",
                "ema200": "h1_ema200",
                "ema50": "h1_ema50",
                "ema50_lag6": "h1_ema50_lag6",
            }
        ),
        on="time",
        direction="backward",
    )

    trades: list[BacktestTrade] = []
    i = 0
    while i < len(merged) - 1:
        row = merged.iloc[i]
        needed = [
            row["atr14"],
            row["adx14"],
            row["donchian_high20"],
            row["donchian_low20"],
            row["h1_ema200"],
            row["h1_ema50"],
            row["h1_ema50_lag6"],
        ]
        if any(pd.isna(v) for v in needed):
            i += 1
            continue

        atr_now = float(row["atr14"])
        buffer = breakout_buffer_atr * atr_now

        long_signal = (
            row["h1_close"] > row["h1_ema200"]
            and row["h1_ema50"] > row["h1_ema50_lag6"]
            and row["adx14"] > adx_threshold
            and row["close"] > row["donchian_high20"] + buffer
        )
        short_signal = (
            row["h1_close"] < row["h1_ema200"]
            and row["h1_ema50"] < row["h1_ema50_lag6"]
            and row["adx14"] > adx_threshold
            and row["close"] < row["donchian_low20"] - buffer
        )

        if not long_signal and not short_signal:
            i += 1
            continue

        side = "buy" if long_signal else "sell"
        entry_i = i + 1
        entry_row = merged.iloc[entry_i]
        entry = float(entry_row["open"])
        risk_distance = stop_atr * atr_now

        if side == "buy":
            stop = entry - risk_distance
            target = entry + target_r * risk_distance
        else:
            stop = entry + risk_distance
            target = entry - target_r * risk_distance

        exit_price = float(entry_row["close"])
        exit_reason = "time"
        exit_i = min(entry_i + max_holding_bars - 1, len(merged) - 1)

        for j in range(entry_i, exit_i + 1):
            bar = merged.iloc[j]
            if side == "buy":
                stop_hit = float(bar["low"]) <= stop
                target_hit = float(bar["high"]) >= target
            else:
                stop_hit = float(bar["high"]) >= stop
                target_hit = float(bar["low"]) <= target

            # Conservative ambiguity rule: if both are touched in the same OHLC bar,
            # count the stop first unless tick ordering later proves otherwise.
            if stop_hit:
                exit_price = stop
                exit_reason = "stop"
                exit_i = j
                break
            if target_hit:
                exit_price = target
                exit_reason = "target"
                exit_i = j
                break

            exit_price = float(bar["close"])

        if side == "buy":
            gross_r = (exit_price - entry) / risk_distance
        else:
            gross_r = (entry - exit_price) / risk_distance

        net_r = gross_r - round_trip_cost_r
        trades.append(
            BacktestTrade(
                side=side,
                entry_time=str(entry_row["time"]),
                exit_time=str(merged.iloc[exit_i]["time"]),
                entry=entry,
                stop=stop,
                target=target,
                exit=exit_price,
                gross_r=gross_r,
                cost_r=round_trip_cost_r,
                net_r=net_r,
                exit_reason=exit_reason,
            )
        )
        i = exit_i + 1

    metrics = performance_metrics([t.net_r for t in trades])
    return {
        "strategy": "mtf_breakout_v1",
        "parameters": {
            "adx_threshold": adx_threshold,
            "breakout_buffer_atr": breakout_buffer_atr,
            "stop_atr": stop_atr,
            "target_r": target_r,
            "max_holding_bars": max_holding_bars,
            "round_trip_cost_r": round_trip_cost_r,
        },
        "metrics": metrics.to_dict(),
        "trades": [t.to_dict() for t in trades],
        "assumptions": {
            "entry": "next M15 bar open after completed signal bar",
            "intrabar_ambiguity": "stop_first_conservative",
            "cost_model": "fixed round-trip cost in R",
            "live_claim": False,
        },
    }
