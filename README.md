# GoldBot AI

GoldBot AI is a research-first XAUUSD trading platform built around the attached project research: H1 regime/trend filtering, M15 breakout/pullback execution, broker-aware ATR risk, strict drawdown controls, MT5 connectivity, reproducible backtests, and an AI research layer.

## What is implemented

### Trading engine
- MetaTrader 5 account/tick/bar connectivity
- broker symbol specifications
- broker-aware `order_calc_profit` sizing
- H1 trend + M15 Donchian/ADX breakout strategy
- completed-bar decisioning
- spread percentile and stale-data gates
- economic-news gate
- deterministic market-regime classifier
- server-side stop/TP order validation
- guarded demo/live execution authorization
- one GoldBot directional position at a time
- +1R trailing protection
- three-hour time exit when trailing has not activated
- persistent bar de-duplication to avoid repeated entries after restart

### Risk
- default 0.25% research risk per trade
- configurable 0.10–0.25% live range
- daily loss stop
- weekly loss stop
- soft drawdown risk reduction
- hard drawdown kill switch
- three-loss pause
- no martingale
- no averaging down
- no grid recovery
- repeated DB audit failures fail closed in demo/live mode

### Research
- conservative OHLC backtester
- stop-first ambiguity rule when tick order is unknown
- broker-tick collection to compressed Parquet
- tick-level stop/target replay utility
- parameter-grid research
- chronological development/validation/OOS/2026 holdout evaluation
- walk-forward evaluation
- normal/stress execution-cost runs
- bootstrap Monte Carlo
- experiment registry
- research notes
- nightly research-cycle script
- strategy promotion gates

### AI / ML
- chronological logistic-regression meta-label baseline
- deterministic feature schema
- model version registry
- observer-only training API
- AI cannot create trades on its own
- unapproved AI cannot block the mechanical strategy
- only explicitly approved validated models may act as a filter

### Operations
- PostgreSQL audit/research schema
- trade/order/risk/heartbeat/error records
- dark authenticated dashboard
- FastAPI API
- Windows MT5 runner
- MQL5 safety-EA scaffold
- GitHub Actions tests
- Windows research scheduled-task installer

## Safety defaults

```env
TRADING_MODE=research
LIVE_TRADING_ENABLED=false
RISK_PER_TRADE=0.0025
DAILY_LOSS_LIMIT=0.01
WEEKLY_LOSS_LIMIT=0.025
SOFT_DRAWDOWN_LIMIT=0.08
HARD_DRAWDOWN_LIMIT=0.10
```

There is deliberately no logic that increases risk to chase an R500 daily target.

## Local research/dashboard

```powershell
git clone https://github.com/leeroyimpilo-web/goldbot.git
cd goldbot

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,mt5]"

Copy-Item .env.example .env
docker compose up -d postgres

uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/dashboard`.

The development example credentials are `goldbot / change-me`. Replace them before exposing the dashboard to any network.

Initialize the DB from the dashboard or:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/database/init -Credential (Get-Credential)
```

## Continuous bot runner

MetaTrader 5 must be installed and logged into the intended broker account on the same Windows VPS.

```powershell
python -m app.runner
```

Research mode never sends orders.

Demo execution requires:
- `TRADING_MODE=demo`
- MT5 reports a demo account
- strategy is registered at demo stage

Live execution additionally requires:
- `TRADING_MODE=live`
- `LIVE_TRADING_ENABLED=true`
- MT5 reports a real account
- strategy is at `small_live` or `live` stage
- `live_approved=true`
- all health/risk/news/spread/order checks pass

## Research cycle

```powershell
python -m app.research_cycle
```

Or install the nightly Windows task:

```powershell
.\scripts\install_research_task.ps1
```

This cycle can create research candidates and notes but cannot promote itself into demo/live trading.

## Important

Backtests and ML outputs are evidence-generation tools, not guarantees of future profit. Do not enable live trading until broker-specific historical testing, 2026 holdout evaluation, stress testing and a substantial demo-forward period have met the project acceptance gates.

See:
- `docs/ARCHITECTURE.md`
- `docs/DEPLOYMENT.md`
