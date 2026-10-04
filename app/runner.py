from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time

from app.config import settings
from app.decision_engine import DecisionEngine
from app.execution import ExecutionManager
from app.mt5_gateway import MT5Gateway
from app.position_manager import manage_position
from app.runtime_risk import update_runtime_risk
from app.strategy_registry import is_strategy_approved
from app.trade_planner import TradePlan

log = logging.getLogger("goldbot.runner")
STATE_PATH = Path("runtime_state.json")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state: dict) -> None:
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def run_cycle(
    gateway: MT5Gateway,
    decision_engine: DecisionEngine,
    execution_manager: ExecutionManager,
    state: dict,
) -> dict:
    account = gateway.account_snapshot()
    if not account.get("available"):
        return {"status": "blocked", "reason": "account_unavailable"}

    risk_metrics = update_runtime_risk(
        state,
        equity=float(account["equity"]),
    )

    open_positions = gateway.open_positions()
    goldbot_positions = [
        p for p in open_positions
        if int(p.get("magic", 0)) == 260100
    ]
    if goldbot_positions:
        position = goldbot_positions[0]
        management = manage_position(
            gateway,
            position,
            state.get("active_plan"),
        )
        if state.get("active_plan"):
            state["active_plan"]["last_management"] = management
        save_state(state)
        return {
            "status": "manage_only",
            "reason": "existing_goldbot_position",
            "position": position,
            "management": management,
            "risk": risk_metrics.to_dict(),
        }

    if state.get("active_plan") is not None:
        state["last_closed_plan"] = state.pop("active_plan")
        state["last_closed_plan"]["closed_detected_at"] = datetime.now(timezone.utc).isoformat()

        recent = gateway.recent_closed_goldbot_deals(days=30)
        consecutive_losses = 0
        for deal in reversed(recent):
            if float(deal.get("net_profit", 0.0)) < 0:
                consecutive_losses += 1
            else:
                break
        state["consecutive_full_stop_losses"] = consecutive_losses
        state["last_closed_deal"] = recent[-1] if recent else None
        save_state(state)

    latest_bar = gateway.latest_completed_bar_time("M15")
    if latest_bar is None:
        save_state(state)
        return {"status": "blocked", "reason": "m15_bar_unavailable"}

    if state.get("last_processed_m15_bar") == latest_bar:
        save_state(state)
        return {
            "status": "idle",
            "reason": "bar_already_processed",
            "bar": latest_bar,
            "risk": risk_metrics.to_dict(),
        }

    state["last_processed_m15_bar"] = latest_bar
    save_state(state)

    decision = decision_engine.evaluate(
        daily_return=risk_metrics.daily_return,
        weekly_return=risk_metrics.weekly_return,
        drawdown=risk_metrics.drawdown,
        consecutive_full_stop_losses=int(state.get("consecutive_full_stop_losses", 0)),
    )
    if decision.get("status") != "candidate":
        save_state(state)
        return decision

    plan = TradePlan(**decision["plan"])
    approved = is_strategy_approved(
        plan.strategy_version,
        settings.trading_mode,
    )
    execution = execution_manager.submit(
        plan,
        strategy_approved=approved,
    )

    if execution.get("sent"):
        state["active_plan"] = {
            **plan.to_dict(),
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "trailing_activated": False,
            "execution": execution.get("result", {}),
        }
        save_state(state)

    return {
        "status": "execution_attempt",
        "decision": decision,
        "execution": execution,
        "risk": risk_metrics.to_dict(),
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    gateway = MT5Gateway()
    decision_engine = DecisionEngine(gateway)
    execution_manager = ExecutionManager(gateway)
    state = load_state()

    log.info(
        "GoldBot runner starting: mode=%s live_flag=%s symbol=%s",
        settings.trading_mode,
        settings.live_trading_enabled,
        settings.symbol,
    )

    while True:
        try:
            result = run_cycle(
                gateway,
                decision_engine,
                execution_manager,
                state,
            )
            log.info("cycle=%s", result.get("status"))
        except KeyboardInterrupt:
            raise
        except Exception:
            log.exception("GoldBot cycle failed")
        time.sleep(10)


if __name__ == "__main__":
    main()
