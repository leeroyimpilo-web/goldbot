from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PromotionDecision:
    approved: bool
    target_stage: str
    reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_research_to_demo(
    *,
    oos_profit_factor: float | None,
    oos_expectancy_r: float,
    oos_max_drawdown_pct: float,
    stress_profit_factor: float | None,
    profitable_years: int,
    required_profitable_years: int = 3,
    parameter_stable: bool,
    best_trades_dependency_ok: bool,
) -> PromotionDecision:
    reasons: list[str] = []

    if oos_profit_factor is None or oos_profit_factor < 1.20:
        reasons.append("oos_profit_factor_below_1.20")
    if oos_expectancy_r <= 0:
        reasons.append("oos_expectancy_not_positive")
    if oos_max_drawdown_pct > 8.0:
        reasons.append("oos_drawdown_above_8pct")
    if stress_profit_factor is None or stress_profit_factor <= 1.0:
        reasons.append("stress_profit_factor_not_above_1.0")
    if profitable_years < required_profitable_years:
        reasons.append("insufficient_profitable_years")
    if not parameter_stable:
        reasons.append("parameter_surface_unstable")
    if not best_trades_dependency_ok:
        reasons.append("depends_too_heavily_on_best_trades")

    return PromotionDecision(
        approved=not reasons,
        target_stage="demo" if not reasons else "research",
        reasons=reasons or ["all_research_to_demo_gates_passed"],
    )


def evaluate_demo_to_live(
    *,
    demo_trading_days: int,
    demo_trades: int,
    risk_rule_violations: int,
    unexplained_position_mismatches: int,
    slippage_model_compatible: bool,
    kill_switch_tests_passed: bool,
    restart_recovery_passed: bool,
) -> PromotionDecision:
    reasons: list[str] = []

    if demo_trading_days < 60:
        reasons.append("demo_less_than_60_trading_days")
    if demo_trades < 100:
        reasons.append("demo_less_than_100_trades")
    if risk_rule_violations != 0:
        reasons.append("risk_rule_violations_present")
    if unexplained_position_mismatches != 0:
        reasons.append("position_mismatches_present")
    if not slippage_model_compatible:
        reasons.append("slippage_not_compatible_with_model")
    if not kill_switch_tests_passed:
        reasons.append("kill_switch_tests_failed")
    if not restart_recovery_passed:
        reasons.append("restart_recovery_failed")

    return PromotionDecision(
        approved=not reasons,
        target_stage="small_live" if not reasons else "demo",
        reasons=reasons or ["all_demo_to_live_gates_passed"],
    )
