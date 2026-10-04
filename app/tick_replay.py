from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

import pandas as pd


@dataclass(frozen=True)
class TickExit:
    exit_time: str
    exit_price: float
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def resolve_exit_with_ticks(
    ticks: pd.DataFrame,
    *,
    side: str,
    stop: float,
    target: float,
    entry_time: datetime,
    max_exit_time: datetime,
) -> TickExit | None:
    required = {"timestamp_utc", "bid", "ask"}
    if not required.issubset(ticks.columns):
        raise ValueError(f"Tick frame missing required columns: {required - set(ticks.columns)}")
    if side not in {"buy", "sell"}:
        raise ValueError("side must be buy or sell")

    frame = ticks[
        (ticks["timestamp_utc"] >= entry_time)
        & (ticks["timestamp_utc"] <= max_exit_time)
    ].sort_values("timestamp_utc")

    if frame.empty:
        return None

    for _, tick in frame.iterrows():
        if side == "buy":
            executable = float(tick["bid"])
            if executable <= stop:
                return TickExit(str(tick["timestamp_utc"]), executable, "stop")
            if executable >= target:
                return TickExit(str(tick["timestamp_utc"]), executable, "target")
        else:
            executable = float(tick["ask"])
            if executable >= stop:
                return TickExit(str(tick["timestamp_utc"]), executable, "stop")
            if executable <= target:
                return TickExit(str(tick["timestamp_utc"]), executable, "target")

    last = frame.iloc[-1]
    executable = float(last["bid"] if side == "buy" else last["ask"])
    return TickExit(str(last["timestamp_utc"]), executable, "time")
