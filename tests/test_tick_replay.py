from datetime import datetime, timedelta, timezone

import pandas as pd

from app.tick_replay import resolve_exit_with_ticks


def test_tick_order_resolves_target_before_later_stop():
    start = datetime(2026, 10, 4, 10, 0, tzinfo=timezone.utc)
    ticks = pd.DataFrame(
        {
            "timestamp_utc": [
                start,
                start + timedelta(seconds=1),
                start + timedelta(seconds=2),
            ],
            "bid": [100.0, 102.0, 98.0],
            "ask": [100.1, 102.1, 98.1],
        }
    )
    result = resolve_exit_with_ticks(
        ticks,
        side="buy",
        stop=99.0,
        target=101.5,
        entry_time=start,
        max_exit_time=start + timedelta(minutes=1),
    )
    assert result is not None
    assert result.reason == "target"
