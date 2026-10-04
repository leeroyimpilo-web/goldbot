from __future__ import annotations

from app.database import (
    Heartbeat,
    OrderRecord,
    RiskSnapshot,
    SessionLocal,
    SystemError,
)
from app.trade_planner import TradePlan


def _commit(row) -> bool:
    try:
        with SessionLocal() as session:
            session.add(row)
            session.commit()
        return True
    except Exception:
        return False


def record_heartbeat(component: str, status: str, details: dict | None = None) -> bool:
    return _commit(
        Heartbeat(
            component=component,
            status=status,
            details=details or {},
        )
    )


def record_risk_snapshot(
    *,
    equity: float,
    balance: float,
    daily_return: float,
    weekly_return: float,
    drawdown: float,
    consecutive_losses: int,
    trading_allowed: bool,
    reason: str | None = None,
) -> bool:
    return _commit(
        RiskSnapshot(
            equity=equity,
            balance=balance,
            daily_return=daily_return,
            weekly_return=weekly_return,
            drawdown=drawdown,
            consecutive_losses=consecutive_losses,
            trading_allowed=trading_allowed,
            reason=reason,
        )
    )


def record_order_attempt(
    *,
    plan: TradePlan,
    execution: dict,
) -> bool:
    result = execution.get("result") or {}
    return _commit(
        OrderRecord(
            strategy_version=plan.strategy_version,
            symbol="XAUUSD",
            side=plan.side,
            volume=plan.volume,
            requested_price=plan.entry,
            stop_price=plan.stop,
            target_price=plan.target,
            broker_order_id=str(result.get("order")) if result.get("order") else None,
            broker_deal_id=str(result.get("deal")) if result.get("deal") else None,
            status="sent" if execution.get("sent") else "rejected",
            request_payload=plan.to_dict(),
            response_payload=execution,
        )
    )


def record_system_error(
    component: str,
    error: Exception,
    details: dict | None = None,
) -> bool:
    return _commit(
        SystemError(
            component=component,
            error_type=type(error).__name__,
            message=str(error),
            details=details or {},
        )
    )
