# GoldBot Windows VPS Deployment

## Requirements

- Windows Server/Windows 11 VPS
- MetaTrader 5 installed
- Broker account logged into MT5
- Python 3.12
- PostgreSQL reachable from the VPS

## Install

```powershell
git clone https://github.com/leeroyimpilo-web/goldbot.git
cd goldbot
.\scripts\run_goldbot_windows.ps1
```

The first invocation creates `.env` and stops so credentials/settings can be reviewed.

## Safe initial settings

```env
TRADING_MODE=research
LIVE_TRADING_ENABLED=false
RISK_PER_TRADE=0.0025
DAILY_LOSS_LIMIT=0.01
WEEKLY_LOSS_LIMIT=0.025
SOFT_DRAWDOWN_LIMIT=0.08
HARD_DRAWDOWN_LIMIT=0.10
REQUIRE_AUTH=true
DASHBOARD_USERNAME=goldbot
DASHBOARD_PASSWORD=REPLACE_WITH_A_LONG_RANDOM_PASSWORD
```

Run the API:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Initialize the database using the authenticated dashboard/API, then run the research backtests before registering any strategy above research stage.

## Demo mode

Only switch to:

```env
TRADING_MODE=demo
```

after the strategy is registered as demo-approved. Execution authorization also verifies that MT5 reports a demo account.

## Live mode

Live mode requires all of the following simultaneously:

- `TRADING_MODE=live`
- `LIVE_TRADING_ENABLED=true`
- MT5 reports a real-money account
- strategy stage is small_live or live
- strategy has `live_approved=true`
- risk and order checks pass

Do not use live mode until historical, out-of-sample, stress, Monte Carlo and forward-demo evidence have met the project gates.
