from __future__ import annotations

import logging

from app.backtest import run_mtf_breakout_backtest
from app.database import init_db
from app.experiments import make_experiment
from app.monte_carlo import bootstrap_monte_carlo
from app.mt5_gateway import MT5Gateway
from app.research import parameter_grid_search, research_score
from app.research_store import save_experiment, save_research_note

log = logging.getLogger("goldbot.research_cycle")


def run_research_cycle(
    gateway: MT5Gateway,
    *,
    h1_bars: int = 5000,
    m15_bars: int = 20000,
    normal_cost_r: float = 0.05,
    stress_cost_r: float = 0.10,
) -> dict:
    h1 = gateway.bars("H1", h1_bars)
    m15 = gateway.bars("M15", m15_bars)
    if h1.empty or m15.empty:
        return {"ok": False, "reason": "market_history_unavailable"}

    baseline = run_mtf_breakout_backtest(
        h1,
        m15,
        round_trip_cost_r=normal_cost_r,
    )
    stress = run_mtf_breakout_backtest(
        h1,
        m15,
        round_trip_cost_r=stress_cost_r,
    )

    grid = parameter_grid_search(
        h1,
        m15,
        cost_r=normal_cost_r,
        top_n=10,
    )

    top = grid["top"][0] if grid["top"] else None
    saved_experiment = None
    if top:
        experiment = make_experiment(
            strategy_name="mtf_breakout",
            strategy_version="mtf_breakout_v1",
            stage="research",
            parameters=top["parameters"],
            metrics=top["metrics"],
            notes="Automated research-cycle candidate. Research-only; no self-promotion.",
        )
        saved_experiment = save_experiment(
            experiment,
            score=research_score(top["metrics"]),
        )

    mc = None
    returns = [float(t["net_r"]) for t in baseline["trades"]]
    if len(returns) >= 20:
        mc = bootstrap_monte_carlo(
            returns,
            paths=5000,
        ).to_dict()

    observation = (
        f"Baseline PF={baseline['metrics']['profit_factor']}, "
        f"expectancy={baseline['metrics']['expectancy_r']:.4f}R, "
        f"stress PF={stress['metrics']['profit_factor']}. "
        f"Grid tested {grid['tested']} variants with {grid['survivors']} positive survivors."
    )
    recommendation = (
        "Keep all candidates in research until chronological OOS, stress, "
        "Monte Carlo and demo gates pass."
    )
    note_id = save_research_note(
        category="automated_research_cycle",
        title="MTF breakout research update",
        observation=observation,
        evidence={
            "baseline_metrics": baseline["metrics"],
            "stress_metrics": stress["metrics"],
            "grid_top": top,
            "monte_carlo": mc,
        },
        recommendation=recommendation,
        strategy_version="mtf_breakout_v1",
    )

    return {
        "ok": True,
        "baseline": baseline["metrics"],
        "stress": stress["metrics"],
        "grid": {
            "tested": grid["tested"],
            "survivors": grid["survivors"],
            "top": grid["top"],
        },
        "monte_carlo": mc,
        "saved_experiment_id": saved_experiment,
        "research_note_id": note_id,
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    init_db()
    gateway = MT5Gateway()
    result = run_research_cycle(gateway)
    if not result.get("ok"):
        raise SystemExit(f"Research cycle failed: {result}")
    log.info("Research cycle complete: %s", result)


if __name__ == "__main__":
    main()
