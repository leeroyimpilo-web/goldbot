from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.config import settings
from app.mt5_gateway import MT5Gateway
from app.trade_planner import TradePlan


@dataclass(frozen=True)
class ExecutionAuthorization:
    allowed: bool
    mode: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def authorize_execution(
    *,
    broker_trade_mode: str,
    strategy_approved: bool,
) -> ExecutionAuthorization:
    mode = settings.trading_mode.lower()

    if mode == "research":
        return ExecutionAuthorization(False, mode, "research_mode_never_sends_orders")

    if not strategy_approved:
        return ExecutionAuthorization(False, mode, "strategy_not_approved")

    if mode == "demo":
        if broker_trade_mode != "demo":
            return ExecutionAuthorization(False, mode, "demo_mode_requires_demo_broker_account")
        return ExecutionAuthorization(True, mode, "demo_execution_authorized")

    if mode == "live":
        if not settings.live_trading_enabled:
            return ExecutionAuthorization(False, mode, "live_trading_flag_disabled")
        if broker_trade_mode != "real":
            return ExecutionAuthorization(False, mode, "live_mode_requires_real_broker_account")
        return ExecutionAuthorization(True, mode, "live_execution_authorized")

    return ExecutionAuthorization(False, mode, "unsupported_trading_mode")


class ExecutionManager:
    def __init__(self, gateway: MT5Gateway) -> None:
        self.gateway = gateway

    def submit(self, plan: TradePlan, *, strategy_approved: bool) -> dict[str, Any]:
        account = self.gateway.account_snapshot()
        if not account.get("available"):
            return {"sent": False, "reason": "account_unavailable"}

        auth = authorize_execution(
            broker_trade_mode=str(account.get("trade_mode", "unknown")),
            strategy_approved=strategy_approved,
        )
        if not auth.allowed:
            return {"sent": False, "authorization": auth.to_dict()}

        check = self.gateway.check_market_order(plan)
        if not check.get("ok"):
            return {
                "sent": False,
                "authorization": auth.to_dict(),
                "order_check": check,
                "reason": "order_check_failed",
            }

        result = self.gateway.send_market_order(plan)
        return {
            "sent": bool(result.get("ok")),
            "authorization": auth.to_dict(),
            "order_check": check,
            "result": result,
        }
