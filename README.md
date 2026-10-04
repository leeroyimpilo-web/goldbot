# GoldBot AI

GoldBot AI is a research-first XAUUSD trading platform designed around strict risk control, reproducible strategy research, MetaTrader 5 connectivity, and a future AI strategy-lab layer.

## Current foundation

- FastAPI backend
- Dark monitoring dashboard
- PostgreSQL database models
- MetaTrader 5 gateway shell
- Initial H1 trend + M15 breakout strategy
- Conservative risk engine
- Unit tests for strategy/risk logic
- Live execution disabled by default

## Safety defaults

GoldBot deliberately prevents target-chasing behavior.

- No martingale
- No averaging down
- No recovery grid
- No automatic risk increase because daily profit is below a target
- New entries blocked during risk-limit, stale-data, abnormal-spread, extreme-volatility, or news-blackout states
- Hard drawdown kill switch
- AI may research and rank strategies, but may not silently promote itself to live trading

## Initial strategy

Primary research candidate:

- H1 close above/below EMA200
- H1 EMA50 slope confirms direction
- M15 ADX > 22
- M15 Donchian 20-bar breakout with 0.05 ATR buffer
- Future execution layer will add ATR/structure stop, 1.8R target, +1R trailing protection, spread/news gates and broker-aware lot sizing

## Local development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
docker compose up -d postgres
uvicorn app.main:app --reload
```

Open:

- API: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Dashboard: http://127.0.0.1:8000/dashboard

## MetaTrader 5

On a Windows MT5 host:

```bash
pip install -e ".[mt5]"
```

MetaTrader 5 must be installed and logged into the intended broker account on the same Windows machine.

## Trading modes

`TRADING_MODE=research` is the default.

Live execution requires both:

```env
TRADING_MODE=live
LIVE_TRADING_ENABLED=true
```

Those flags alone will not be sufficient once the execution module is added; strategy approval and risk gates will also be required.

## Next phases

1. Market-data collector and indicator engine
2. Broker-aware sizing and order validation
3. Event-driven backtester
4. Walk-forward and Monte Carlo research
5. Strategy registry/promotion workflow
6. AI meta-labeling and regime analysis
7. Demo-trading execution manager
8. MQL5 safety EA
