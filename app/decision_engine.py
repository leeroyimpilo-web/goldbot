from __future__ import annotations

from dataclasses import asdict

from app.indicators import build_market_snapshot
from app.mt5_gateway import MT5Gateway
from app.regime import classify_regime
from app.risk import RiskState, evaluate_risk
from app.strategy import MTFBreakoutV1
from app.trade_planner import build_trade_plan


class DecisionEngine:
    def __init__(self, gateway: MT5Gateway) -> None:
        self.gateway = gateway
        self.strategy = MTFBreakoutV1()

    def evaluate(self) -> dict:
        account = self.gateway.account_snapshot()
        if not account.get("available"):
            return {"status": "blocked", "reason": "account_unavailable", "account": account}

        tick = self.gateway.tick()
        if not tick.get("available"):
            return {"status": "blocked", "reason": "tick_unavailable", "tick": tick}

        h1 = self.gateway.bars("H1", 600)
        m15 = self.gateway.bars("M15", 300)
        if h1.empty or m15.empty:
            return {"status": "blocked", "reason": "market_history_unavailable"}

        snapshot = build_market_snapshot(h1, m15)
        regime = classify_regime(h1)

        if not regime.allow_new_entries:
            return {
                "status": "no_trade",
                "reason": f"regime_{regime.name.lower()}",
                "regime": asdict(regime),
                "market": asdict(snapshot),
            }

        signal = self.strategy.generate(snapshot)
        if signal is None:
            return {
                "status": "no_trade",
                "reason": "strategy_no_signal",
                "regime": asdict(regime),
                "market": asdict(snapshot),
            }

        spread = float(tick["ask"] - tick["bid"])
        median_spread = self.gateway.recent_median_spread(points=250)
        spread_ratio = spread / median_spread if median_spread and median_spread > 0 else 1.0

        risk = evaluate_risk(
            RiskState(
                equity=float(account["equity"]),
                daily_return=0.0,
                weekly_return=0.0,
                drawdown=0.0,
                broker_connected=True,
                data_fresh=True,
                news_blackout=False,
                extreme_volatility=regime.name == "EXTREME_VOL",
                spread_ratio=spread_ratio,
            )
        )
        if not risk.allowed:
            return {
                "status": "blocked",
                "reason": risk.reason,
                "regime": asdict(regime),
                "risk": asdict(risk),
                "spread_ratio": spread_ratio,
            }

        executable_entry = float(tick["ask"] if signal.side == "buy" else tick["bid"])
        proposed_stop = (
            executable_entry - 1.2 * signal.atr
            if signal.side == "buy"
            else executable_entry + 1.2 * signal.atr
        )

        loss_per_lot = self.gateway.loss_per_lot(
            side=signal.side,
            entry=executable_entry,
            stop=proposed_stop,
        )
        specs = self.gateway.symbol_specs()
        if not specs.get("available"):
            return {"status": "blocked", "reason": "symbol_specs_unavailable", "details": specs}

        effective_risk = type(risk)(
            allowed=risk.allowed,
            reason=risk.reason,
            risk_pct=risk.risk_pct * regime.risk_multiplier,
        )
        if effective_risk.risk_pct <= 0:
            return {"status": "no_trade", "reason": "regime_risk_zero", "regime": asdict(regime)}

        plan = build_trade_plan(
            signal=signal,
            strategy_version=self.strategy.version,
            executable_entry=executable_entry,
            equity=float(account["equity"]),
            risk=effective_risk,
            loss_per_lot=loss_per_lot,
            volume_min=float(specs["volume_min"]),
            volume_max=float(specs["volume_max"]),
            volume_step=float(specs["volume_step"]),
        )

        check = self.gateway.check_market_order(plan)
        return {
            "status": "candidate" if check.get("ok") else "blocked",
            "reason": "order_check_passed" if check.get("ok") else "order_check_failed",
            "regime": asdict(regime),
            "risk": asdict(effective_risk),
            "spread_ratio": spread_ratio,
            "plan": plan.to_dict(),
            "order_check": check,
            "execution": "NOT_SENT",
        }
