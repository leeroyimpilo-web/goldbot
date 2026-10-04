from datetime import datetime, timezone

from app.data_lake import tick_partition_path


def test_tick_partition_path_is_date_partitioned():
    path = tick_partition_path(
        "data",
        datetime(2026, 10, 4, tzinfo=timezone.utc),
    )
    assert str(path).endswith("raw_ticks/XAUUSD/2026/10/04.parquet")
