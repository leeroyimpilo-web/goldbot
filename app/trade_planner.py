from dataclasses import asdict, dataclass

from app.risk import RiskDecision
from app.strategy import StrategySignal


@dataclass(frozen=True)
class TradePlan:
    side: str
    entry: float
    stop: float
    target: float
    risk_cash: float
    risk_pct: float
    loss_per_lot: float
    volume: float
    r_target: float
    strategy_version: str
    reason: str

    def to_dict(self) -> dict:
        return asdict(self)


def floor_to_step(value: float, step: float) -> float:
    if step <= 0:
        raise ValueError("Volume step must be positive")
    return max(0.0, (value // step) * step)


def build_trade_plan(
    *,
    signal: StrategySignal,
    strategy_version: str,
    executable_entry: float,
    equity: float,
    risk: RiskDecision,
    loss_per_lot: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
    swing_price: float | None = None,
) -> TradePlan:
    if not risk.allowed:
        raise ValueError(f"Risk gate blocked trade: {risk.reason}")
    if loss_per_lot <= 0:
        raise ValueError("Loss per lot must be positive")
    if signal.atr <= 0:
        raise ValueError("ATR must be positive")

    atr_stop = 1.2 * signal.atr

    if signal.side == "buy":
        structure_stop = (
            executable_entry - (max(0.0, executable_entry - swing_price) + 0.1 * signal.atr)
            if swing_price is not None
            else executable_entry - atr_stop
        )
        stop = min(executable_entry - atr_stop, structure_stop)
        risk_distance = executable_entry - stop
        target = executable_entry + 1.8 * risk_distance
    elif signal.side == "sell":
        structure_stop = (
            executable_entry + (max(0.0, swing_price - executable_entry) + 0.1 * signal.atr)
            if swing_price is not None
            else executable_entry + atr_stop
        )
        stop = max(executable_entry + atr_stop, structure_stop)
        risk_distance = stop - executable_entry
        target = executable_entry - 1.8 * risk_distance
    else:
        raise ValueError(f"Unsupported side: {signal.side}")

    risk_cash = equity * risk.risk_pct
    raw_volume = risk_cash / loss_per_lot
    volume = floor_to_step(min(raw_volume, volume_max), volume_step)

    if volume < volume_min:
        raise ValueError("Calculated volume is below broker minimum")

    return TradePlan(
        side=signal.side,
        entry=executable_entry,
        stop=stop,
        target=target,
        risk_cash=risk_cash,
        risk_pct=risk.risk_pct,
        loss_per_lot=loss_per_lot,
        volume=volume,
        r_target=1.8,
        strategy_version=strategy_version,
        reason=signal.reason,
    )
