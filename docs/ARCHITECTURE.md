# GoldBot Architecture

## Runtime

GoldBot is designed to run on a Windows VPS beside MetaTrader 5.

The production path is:

1. MT5 broker feed provides broker-specific XAUUSD bars, ticks, account information and execution.
2. GoldBot builds indicators and classifies the market regime.
3. The mechanical strategy creates a candidate signal only from completed bars.
4. News, spread, data health and account-risk gates can reject the signal.
5. Broker-aware sizing uses MT5 profit calculations rather than hard-coded pip values.
6. MT5 order_check validates a candidate before any send.
7. Execution authorization separately enforces research/demo/live mode and strategy approval.
8. PostgreSQL stores signals, trades, risk events, backtests, experiments and AI model history.
9. The dashboard displays status, research results and experiment history.

## AI role

The first ML model is a chronological logistic-regression meta-labeler. Its purpose is not to invent trades. It estimates whether an already-valid mechanical setup is likely to reach its profit objective before its stop.

An unapproved AI model is observer-only and cannot block or create trades. A model must be explicitly promoted before its output can become an execution filter.

## Research progression

research -> validation -> out-of-sample -> holdout -> demo -> small live -> controlled scale

No strategy is allowed to promote itself.

## Process isolation

The FastAPI dashboard and the continuous runner may be separate processes on the same Windows VPS.

- API: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Runner: `python -m app.runner`

The MQL5 Safety EA is a separate broker-terminal fail-safe layer and contains no autonomous entry strategy.
