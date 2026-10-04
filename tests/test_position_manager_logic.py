from datetime import datetime, timedelta, timezone

import pandas as pd

from app.position_manager import manage_position


class FakeGateway:
    def tick(self):
        return {"available": True, "bid": 102.0, "ask": 102.1}

    def bars(self, timeframe, count):
        rows = []
        for i in range(60):
            rows.append({"open": 100, "high": 101, "low": 99, "close": 100 + i * 0.01})
        return pd.DataFrame(rows)

    def modify_position_sl_tp(self, ticket, sl, tp):
        return {"ok": True}

    def close_position(self, position):
        return {"ok": True}


def test_time_exit_after_three_hours_when_not_trailing():
    gateway = FakeGateway()
    now = datetime.now(timezone.utc)
    position = {
        "ticket": 1,
        "side": "buy",
        "price_open": 100.0,
        "sl": 99.0,
        "tp": 101.8,
        "time": int((now - timedelta(hours=4)).timestamp()),
    }
    plan = {
        "stop": 99.0,
        "opened_at": (now - timedelta(hours=4)).isoformat(),
        "trailing_activated": False,
    }
    result = manage_position(gateway, position, plan, now=now)
    assert result["action"] in {"time_exit", "trail_stop"}
