from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.config import settings
from app.dashboard import DASHBOARD_HTML
from app.mt5_gateway import MT5Gateway
from app.risk import live_execution_permitted

app = FastAPI(
    title="GoldBot AI",
    version="0.1.0",
    description="Research-first XAUUSD trading, risk and strategy-learning platform.",
)

mt5 = MT5Gateway()


@app.get("/")
def root() -> dict:
    return {"name": "GoldBot AI", "version": "0.1.0", "status": "foundation-online", "docs": "/docs", "dashboard": "/dashboard"}


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


@app.get("/api/mt5/account")
def mt5_account() -> dict:
    return mt5.account_snapshot()


@app.get("/api/mt5/tick")
def mt5_tick() -> dict:
    return mt5.tick()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML
