from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from app.config import settings
from app.mt5_gateway import MT5Gateway


def tick_partition_path(root: str | Path, day: datetime) -> Path:
    day = day.astimezone(timezone.utc)
    return (
        Path(root)
        / "raw_ticks"
        / settings.symbol
        / f"{day.year:04d}"
        / f"{day.month:02d}"
        / f"{day.day:02d}.parquet"
    )


def collect_tick_day(
    gateway: MT5Gateway,
    day: datetime,
    *,
    root: str | Path = "data",
    overwrite: bool = False,
) -> dict:
    day = day.astimezone(timezone.utc)
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    target = tick_partition_path(root, start)

    if target.exists() and not overwrite:
        existing = pd.read_parquet(target)
        return {
            "ok": True,
            "path": str(target),
            "rows": len(existing),
            "skipped": True,
        }

    ticks = gateway.ticks_range(start, end)
    if ticks.empty:
        return {
            "ok": False,
            "path": str(target),
            "rows": 0,
            "reason": "no_ticks_returned",
        }

    target.parent.mkdir(parents=True, exist_ok=True)
    ticks.to_parquet(target, index=False, compression="zstd")
    return {
        "ok": True,
        "path": str(target),
        "rows": len(ticks),
        "skipped": False,
        "start": start.isoformat(),
        "end": end.isoformat(),
    }


def collect_tick_range(
    gateway: MT5Gateway,
    start_day: datetime,
    end_day: datetime,
    *,
    root: str | Path = "data",
    overwrite: bool = False,
) -> dict:
    if start_day.tzinfo is None or end_day.tzinfo is None:
        raise ValueError("Dates must be timezone-aware")
    if end_day < start_day:
        raise ValueError("end_day must not be before start_day")

    cursor = datetime(
        start_day.year,
        start_day.month,
        start_day.day,
        tzinfo=timezone.utc,
    )
    final = datetime(
        end_day.year,
        end_day.month,
        end_day.day,
        tzinfo=timezone.utc,
    )

    partitions = []
    total_rows = 0
    while cursor <= final:
        result = collect_tick_day(
            gateway,
            cursor,
            root=root,
            overwrite=overwrite,
        )
        partitions.append(result)
        total_rows += int(result.get("rows", 0))
        cursor += timedelta(days=1)

    return {
        "ok": all(p.get("ok") for p in partitions),
        "partitions": partitions,
        "total_rows": total_rows,
    }
