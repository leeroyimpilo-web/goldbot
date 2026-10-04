from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from app.backtest import run_mtf_breakout_backtest
from app.config import settings
from app.dashboard import DASHBOARD_HTML
from app.database import init_db
from app.decision_engine import DecisionEngine
from app.experiments import make_experiment
from app.mt5_gateway import MT5Gateway
from app.research import parameter_grid_search, research_score
from app.research_store import (
    recent_experiments,
    recent_research_notes,
    save_backtest,
    save_experiment,
)
from app.risk import live_execution_permitted
from app.walkforward import walk_forward

app = FastAPI(
    title="GoldBot AI",
    version="0.4.0",
    description="Research-first XAUUSD trading, risk and strategy-learning platform.",
)

mt5 = MT5Gateway()
decision_engine = DecisionEngine(mt5)


@app.get("/")
def root() -> dict:
    return {
        "name": "GoldBot AI",
        "version": "0.4.0",
        "status": "research-database-online",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True, "environment": settings.app_env}


@app.get("/api/status")
def status() -> dict:
    return {
        "trading_mode": settings.trading_mode,
        "live_trading_enabled": live_execution_permitted(),
        "symbol": settings.symbol,
        "mt5": mt5.status(),
        "risk_policy": {
            "risk_per_trade": settings.risk_per_trade,
            "daily_loss_limit": settings.daily_loss_limit,
            "weekly_loss_limit": settings.weekly_loss_limit,
            "soft_drawdown_limit": settings.soft_drawdown_limit,
            "hard_drawdown_limit": settings.hard_drawdown_limit,
            "max_spread_ratio": settings.max_spread_ratio,
            "martingale": False,
            "averaging_down": False,
        },
    }


@app.post("/api/database/init")
def database_init() -> dict:
    try:
        init_db()
        return {"ok": True, "message": "GoldBot database schema initialized."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@app.get("/api/mt5/account")
def mt5_account() -> dict:
    return mt5.account_snapshot()


@app.get("/api/mt5/tick")
def mt5_tick() -> dict:
    return mt5.tick()


@app.get("/api/mt5/bars/{timeframe}")
def mt5_bars(timeframe: str, count: int = 100) -> dict:
    frame = mt5.bars(timeframe.upper(), min(max(count, 1), 2000))
    if frame.empty:
        return {"available": False, "bars": []}
    data = frame.copy()
    data["time"] = data["time"].astype(str)
    return {"available": True, "bars": data.to_dict(orient="records")}


@app.get("/api/decision")
def decision() -> dict:
    """
    Build a complete candidate trade decision from MT5 data.

    This endpoint NEVER sends an order. It performs research/paper decisioning
    and broker order validation only.
    """
    return decision_engine.evaluate()


@app.get("/api/backtest/mt5")
def backtest_mt5(
    h1_bars: int = Query(2500, ge=300, le=10000),
    m15_bars: int = Query(10000, ge=1000, le=40000),
    cost_r: float = Query(0.05, ge=0.0, le=1.0),
    include_trades: bool = False,
    save: bool = False,
) -> dict:
    h1 = mt5.bars("H1", h1_bars)
    m15 = mt5.bars("M15", m15_bars)
    if h1.empty or m15.empty:
        return {
            "available": False,
            "reason": "MT5 historical data unavailable",
            "metrics": None,
        }

    result = run_mtf_breakout_backtest(h1, m15, round_trip_cost_r=cost_r)
    result["available"] = True
    result["source"] = "broker_mt5_completed_bars"

    if save:
        try:
            result["database_id"] = save_backtest(
                strategy_version=result["strategy"],
                data_source=result["source"],
                data_start=h1["time"].min().to_pydatetime(),
                data_end=h1["time"].max().to_pydatetime(),
                parameters=result["parameters"],
                metrics=result["metrics"],
                assumptions=result["assumptions"],
            )
        except Exception as exc:
            result["database_error"] = str(exc)

    if not include_trades:
        result["trade_sample"] = result["trades"][-20:]
        result.pop("trades", None)
    return result


@app.get("/api/research/grid")
def research_grid(
    h1_bars: int = Query(2500, ge=300, le=10000),
    m15_bars: int = Query(10000, ge=1000, le=40000),
    cost_r: float = Query(0.05, ge=0.0, le=1.0),
    top_n: int = Query(20, ge=1, le=100),
    save_top: bool = False,
) -> dict:
    h1 = mt5.bars("H1", h1_bars)
    m15 = mt5.bars("M15", m15_bars)
    if h1.empty or m15.empty:
        return {"available": False, "reason": "MT5 historical data unavailable"}

    result = parameter_grid_search(h1, m15, cost_r=cost_r, top_n=top_n)
    result["available"] = True

    if save_top and result["top"]:
        top = result["top"][0]
        experiment = make_experiment(
            strategy_name="mtf_breakout",
            strategy_version="mtf_breakout_v1",
            stage="research",
            parameters=top["parameters"],
            metrics=top["metrics"],
            notes="Top parameter-grid candidate; not approved for live trading.",
        )
        try:
            row_id = save_experiment(
                experiment,
                score=research_score(top["metrics"]),
            )
            result["saved_experiment"] = {
                "database_id": row_id,
                **experiment.to_dict(),
            }
        except Exception as exc:
            result["database_error"] = str(exc)

    return result


@app.get("/api/research/walkforward")
def research_walkforward(
    h1_bars: int = Query(5000, ge=1000, le=15000),
    m15_bars: int = Query(20000, ge=4000, le=60000),
    cost_r: float = Query(0.05, ge=0.0, le=1.0),
) -> dict:
    h1 = mt5.bars("H1", h1_bars)
    m15 = mt5.bars("M15", m15_bars)
    if h1.empty or m15.empty:
        return {"available": False, "reason": "MT5 historical data unavailable"}

    result = walk_forward(
        h1,
        m15,
        parameters={"round_trip_cost_r": cost_r},
    )
    result["available"] = True
    return result


@app.get("/api/research/experiments")
def research_experiments(limit: int = Query(50, ge=1, le=200)) -> dict:
    try:
        return {"ok": True, "experiments": recent_experiments(limit)}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "experiments": []}


@app.get("/api/research/notes")
def research_notes(limit: int = Query(50, ge=1, le=200)) -> dict:
    try:
        return {"ok": True, "notes": recent_research_notes(limit)}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "notes": []}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML
