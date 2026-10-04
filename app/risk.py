from dataclasses import dataclass
from app.config import settings


@dataclass(frozen=True)
class RiskState:
    equity: float
    daily_return: float
    weekly_return: float
    drawdown: float
    consecutive_full_stop_losses: int = 0
    broker_connected: bool = True
    data_fresh: bool = True
    news_blackout: bool = False
    extreme_volatility: bool = False
    spread_ratio: float = 1.0


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str
    risk_pct: float


def evaluate_risk(state: RiskState) -> RiskDecision:
    if not state.broker_connected:
        return RiskDecision(False, "broker_disconnected", 0.0)
    if not state.data_fresh:
        return RiskDecision(False, "stale_market_data", 0.0)
    if state.news_blackout:
        return RiskDecision(False, "high_impact_news_blackout", 0.0)
    if state.extreme_volatility:
        return RiskDecision(False, "extreme_volatility", 0.0)
    if state.spread_ratio > settings.max_spread_ratio:
        return RiskDecision(False, "abnormal_spread", 0.0)
    if state.daily_return <= -settings.daily_loss_limit:
        return RiskDecision(False, "daily_loss_limit", 0.0)
    if state.weekly_return <= -settings.weekly_loss_limit:
        return RiskDecision(False, "weekly_loss_limit", 0.0)
    if state.drawdown >= settings.hard_drawdown_limit:
        return RiskDecision(False, "hard_drawdown_kill_switch", 0.0)
    if state.consecutive_full_stop_losses >= 3:
        return RiskDecision(False, "three_stop_losses_pause", 0.0)

    risk_pct = settings.risk_per_trade
    if state.drawdown >= settings.soft_drawdown_limit:
        risk_pct *= 0.5

    return RiskDecision(True, "risk_checks_passed", risk_pct)


def live_execution_permitted() -> bool:
    return settings.trading_mode == "live" and settings.live_trading_enabled
