from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from app.ai_guard import evaluate_ai_gate
from app.economic_calendar import current_news_gate
from app.indicators import build_market_snapshot
from app.ml_features import current_meta_features
from app.ml_meta import load_model, predict_success_probability
from app.model_registry import latest_approved_model
from app.mt5_gateway import MT5Gateway
from app.regime import classify_regime
from app.risk import RiskState, evaluate_risk
from app.strategy import MTFBreakoutV1
from app.trade_planner import build_trade_plan


class DecisionEngine:
    def __init__(self, gateway: MT5Gateway) -> None:
        self.gateway = gateway
        self.strategy = MTFBreakoutV1()

    def evaluate(
        self,
        *,
        daily_return: float = 0.0,
        weekly_return: float = 0.0,
        drawdown: float = 0.0,
        consecutive_full_stop_losses: int = 0,
    ) -> dict:
        account = self.gateway.account_snapshot()
        if not account.get("available"):
            return {"status": "blocked", "reason": "account_unavailable", "account": account}

        tick = self.gateway.tick()
        if not tick.get("available"):
            return {"status": "blocked", "reason": "tick_unavailable", "tick": tick}

        tick_time = datetime.fromtimestamp(float(tick["time_msc"]) / 1000.0, tz=timezone.utc)
        data_age_seconds = max(0.0, (datetime.now(timezone.utc) - tick_time).total_seconds())
        data_fresh = data_age_seconds <= 30.0

        h1 = self.gateway.bars("H1", 600)
        m15 = self.gateway.bars("M15", 300)
        if h1.empty or m15.empty:
            return {"status": "blocked", "reason": "market_history_unavailable"}

        snapshot = build_market_snapshot(h1, m15)
        regime = classify_regime(h1)
        news_gate = current_news_gate()

        if not regime.allow_new_entries:
            return {
                "status": "no_trade",
                "reason": f"regime_{regime.name.lower()}",
                "regime": asdict(regime),
                "market": asdict(snapshot),
                "news_gate": news_gate.to_dict(),
            }

        signal = self.strategy.generate(snapshot)
        if signal is None:
            return {
                "status": "no_trade",
                "reason": "strategy_no_signal",
                "regime": asdict(regime),
                "market": asdict(snapshot),
                "news_gate": news_gate.to_dict(),
            }

        spread = float(tick["ask"] - tick["bid"])
        median_spread = self.gateway.recent_median_spread(points=250)
        spread_ratio = spread / median_spread if median_spread and median_spread > 0 else 1.0
        spread_percentile = self.gateway.spread_percentile(spread, points=250)

        approved_model = None
        ai_probability = None
        ai_error = None
        try:
            approved_model = latest_approved_model()
        except Exception as exc:
            ai_error = f"model_registry_unavailable:{type(exc).__name__}"

        if approved_model:
            try:
                features = current_meta_features(
                    h1,
                    m15,
                    spread_percentile=spread_percentile,
                    news_proximity_minutes=abs(news_gate.minutes_to_event)
                    if news_gate.minutes_to_event is not None
                    else 999.0,
                )
                model = load_model(approved_model["artifact_path"])
                ai_probability = predict_success_probability(model, features)
            except Exception as exc:
                ai_error = f"approved_model_prediction_failed:{type(exc).__name__}"

        ai_gate = evaluate_ai_gate(
            ai_probability,
            model_approved=approved_model is not None,
        )
        if approved_model is not None and (ai_error or not ai_gate.allowed):
            return {
                "status": "blocked",
                "reason": ai_error or ai_gate.reason,
                "regime": asdict(regime),
                "news_gate": news_gate.to_dict(),
                "ai_gate": ai_gate.to_dict(),
                "ai_model": approved_model,
            }

        risk = evaluate_risk(
            RiskState(
                equity=float(account["equity"]),
                daily_return=daily_return,
                weekly_return=weekly_return,
                drawdown=drawdown,
                consecutive_full_stop_losses=consecutive_full_stop_losses,
                broker_connected=True,
                data_fresh=data_fresh,
                news_blackout=news_gate.blocked,
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
                "data_age_seconds": data_age_seconds,
                "news_gate": news_gate.to_dict(),
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
            return {
                "status": "no_trade",
                "reason": "regime_risk_zero",
                "regime": asdict(regime),
                "news_gate": news_gate.to_dict(),
            }

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
            "risk_state": {
                "daily_return": daily_return,
                "weekly_return": weekly_return,
                "drawdown": drawdown,
                "consecutive_full_stop_losses": consecutive_full_stop_losses,
            },
            "spread_ratio": spread_ratio,
            "spread_percentile": spread_percentile,
            "data_age_seconds": data_age_seconds,
            "news_gate": news_gate.to_dict(),
            "ai_gate": ai_gate.to_dict(),
            "ai_model": approved_model,
            "plan": plan.to_dict(),
            "order_check": check,
            "execution": "NOT_SENT",
        }
