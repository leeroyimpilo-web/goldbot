// GoldBot Safety EA
// Purpose: broker-side fail-safe scaffolding for a future hybrid Python + MQL5 deployment.
// It does not open trades. Python remains responsible for research/strategy decisions.

#property strict
#property version   "0.10"

input long GoldBotMagic = 260100;
input double HardDailyLossPct = 1.0;
input double HardDrawdownPct = 10.0;

double session_start_equity = 0.0;
double equity_peak = 0.0;

int OnInit()
{
   session_start_equity = AccountInfoDouble(ACCOUNT_EQUITY);
   equity_peak = session_start_equity;
   EventSetTimer(1);
   Print("GoldBot Safety EA initialized. No autonomous entries are enabled.");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   EventKillTimer();
}

void OnTick()
{
   UpdateSafetyState();
}

void OnTimer()
{
   UpdateSafetyState();
}

void UpdateSafetyState()
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity > equity_peak)
      equity_peak = equity;

   if(session_start_equity <= 0.0 || equity_peak <= 0.0)
      return;

   double daily_loss_pct = 100.0 * (session_start_equity - equity) / session_start_equity;
   double drawdown_pct = 100.0 * (equity_peak - equity) / equity_peak;

   if(daily_loss_pct >= HardDailyLossPct)
   {
      Print("GOLDBOT SAFETY: daily loss limit reached. Python must block new entries.");
   }

   if(drawdown_pct >= HardDrawdownPct)
   {
      Print("GOLDBOT SAFETY: hard drawdown limit reached. Python must kill strategy.");
   }
}

// Future production additions:
// - heartbeat shared with Python
// - reconcile GoldBotMagic positions
// - verify server-side SL/TP acknowledgement
// - emergency flatten policy
// - persistent daily equity reset at broker/session boundary
// - local trade lock file/global terminal variable
