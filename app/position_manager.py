from __future__ import annotations

from datetime import datetime, timezone

from app.indicators import atr
from app.mt5_gateway import MT5Gateway


def manage_position(
    gateway: MT5Gateway,
    position: dict,
    plan_state: dict | None,
    *,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    tick = gateway.tick()
    if not tick.get("available"):
        return {"ok": False, "action": "none", "reason": "tick_unavailable"}

    bars = gateway.bars("M15", 60)
    if bars.empty:
        return {"ok": False, "action": "none", "reason": "m15_history_unavailable"}

    atr_now = float(atr(bars, 14).iloc[-1])
    if atr_now <= 0:
        return {"ok": False, "action": "none", "reason": "invalid_atr"}

    side = position["side"]
    entry = float(position["price_open"])
    current_sl = float(position.get("sl", 0.0) or 0.0)
    target = float(position.get("tp", 0.0) or 0.0)

    if plan_state:
        original_stop = float(plan_state["stop"])
        opened_at_raw = plan_state.get("opened_at")
        opened_at = (
            datetime.fromisoformat(opened_at_raw.replace("Z", "+00:00"))
            if opened_at_raw
            else datetime.fromtimestamp(float(position["time"]), tz=timezone.utc)
        )
    else:
        original_stop = current_sl
        opened_at = datetime.fromtimestamp(float(position["time"]), tz=timezone.utc)

    original_r = abs(entry - original_stop)
    if original_r <= 0:
        return {"ok": False, "action": "none", "reason": "original_r_unavailable"}

    trailing_activated = bool(plan_state and plan_state.get("trailing_activated", False))

    if side == "buy":
        executable_price = float(tick["bid"])
        favorable = executable_price - entry

        if favorable >= original_r:
            candidate_sl = executable_price - 2.5 * atr_now
            new_sl = max(current_sl, candidate_sl, entry)
            if new_sl > current_sl and new_sl < executable_price:
                result = gateway.modify_position_sl_tp(
                    int(position["ticket"]),
                    new_sl,
                    target,
                )
                if result.get("ok") and plan_state is not None:
                    plan_state["trailing_activated"] = True
                    plan_state["last_trailing_sl"] = new_sl
                return {
                    "ok": bool(result.get("ok")),
                    "action": "trail_stop",
                    "new_sl": new_sl,
                    "result": result,
                }

    else:
        executable_price = float(tick["ask"])
        favorable = entry - executable_price

        if favorable >= original_r:
            candidate_sl = executable_price + 2.5 * atr_now
            floor_sl = current_sl if current_sl > 0 else candidate_sl
            new_sl = min(floor_sl, candidate_sl, entry)
            if (current_sl <= 0 or new_sl < current_sl) and new_sl > executable_price:
                result = gateway.modify_position_sl_tp(
                    int(position["ticket"]),
                    new_sl,
                    target,
                )
                if result.get("ok") and plan_state is not None:
                    plan_state["trailing_activated"] = True
                    plan_state["last_trailing_sl"] = new_sl
                return {
                    "ok": bool(result.get("ok")),
                    "action": "trail_stop",
                    "new_sl": new_sl,
                    "result": result,
                }

    elapsed = now - opened_at
    trailing_activated = bool(plan_state and plan_state.get("trailing_activated", trailing_activated))
    if elapsed.total_seconds() >= 3 * 60 * 60 and not trailing_activated:
        result = gateway.close_position(position)
        return {
            "ok": bool(result.get("ok")),
            "action": "time_exit",
            "elapsed_seconds": elapsed.total_seconds(),
            "result": result,
        }

    return {
        "ok": True,
        "action": "hold",
        "atr": atr_now,
        "elapsed_seconds": elapsed.total_seconds(),
        "trailing_activated": trailing_activated,
    }
