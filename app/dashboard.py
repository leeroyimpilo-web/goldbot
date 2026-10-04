DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>GoldBot AI</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:#070a0f;color:#eef2f7}
header{position:sticky;top:0;z-index:10;padding:20px 26px;border-bottom:1px solid #202733;background:rgba(10,14,20,.96);backdrop-filter:blur(12px)}
h1{margin:0;font-size:25px}.sub{color:#8b98a8;margin-top:4px}
main{padding:22px;max-width:1440px;margin:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}
.card{background:linear-gradient(180deg,#10161f,#0d131b);border:1px solid #232d3a;border-radius:16px;padding:18px;box-shadow:0 8px 30px rgba(0,0,0,.18)}
.label{font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:#8592a3}
.value{font-size:25px;margin-top:8px;font-weight:750}
.ok{color:#66e3a4}.warn{color:#ffd166}.bad{color:#ff6b6b}.muted{color:#8b98a8}
.section{margin-top:16px}
pre{white-space:pre-wrap;word-break:break-word;color:#b9c5d3;font-size:12px;line-height:1.45;margin-bottom:0}
button{background:#172233;color:white;border:1px solid #314158;border-radius:10px;padding:10px 14px;cursor:pointer;margin-right:8px;margin-top:8px}
button:hover{background:#1d2b40}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{text-align:left;padding:9px;border-bottom:1px solid #202936;vertical-align:top}
th{color:#8fa0b5;font-weight:600}
.pill{display:inline-block;padding:4px 8px;border-radius:999px;background:#17202c;border:1px solid #2a3747;font-size:11px}
.small{font-size:12px;color:#9aa7b6}
.hero{display:flex;justify-content:space-between;gap:20px;align-items:center}
@media(max-width:650px){main{padding:14px}.hero{display:block}header{padding:16px}}
</style>
</head>
<body>
<header>
  <div class="hero">
    <div><h1>GoldBot AI</h1><div class="sub">XAUUSD research, risk and MT5 control centre</div></div>
    <div class="small">Research-first • Live execution locked by default</div>
  </div>
</header>
<main>
  <div class="grid">
    <div class="card"><div class="label">Trading Mode</div><div id="mode" class="value warn">...</div></div>
    <div class="card"><div class="label">Live Orders</div><div id="live" class="value">...</div></div>
    <div class="card"><div class="label">MT5</div><div id="mt5" class="value">...</div></div>
    <div class="card"><div class="label">Symbol</div><div id="symbol" class="value">XAUUSD</div></div>
    <div class="card"><div class="label">Balance</div><div id="balance" class="value">—</div></div>
    <div class="card"><div class="label">Equity</div><div id="equity" class="value">—</div></div>
  </div>

  <div class="section two">
    <div class="card">
      <div class="label">Current Decision</div>
      <div id="decisionStatus" class="value">—</div>
      <div id="decisionReason" class="small"></div>
      <pre id="decision">Load a decision to inspect the current strategy state.</pre>
      <button onclick="loadDecision()">Evaluate Market</button>
    </div>
    <div class="card">
      <div class="label">Risk Policy</div>
      <pre id="risk">Loading...</pre>
    </div>
  </div>

  <div class="section two">
    <div class="card">
      <div class="label">Quick Backtest</div>
      <div class="small">Uses broker MT5 completed H1/M15 bars. No performance is assumed until measured.</div>
      <pre id="backtest">Not run.</pre>
      <button onclick="runBacktest()">Run Backtest</button>
    </div>
    <div class="card">
      <div class="label">Research Lab</div>
      <div class="small">Parameter search is research-only and never promotes itself to live trading.</div>
      <pre id="research">No research run loaded.</pre>
      <button onclick="loadExperiments()">Load Experiments</button>
    </div>
  </div>

  <div class="section card">
    <div class="label">Saved Experiments</div>
    <div style="overflow:auto">
      <table>
        <thead><tr><th>Created</th><th>Strategy</th><th>Stage</th><th>PF</th><th>Expectancy R</th><th>Score</th><th>Parameters</th></tr></thead>
        <tbody id="experiments"><tr><td colspan="7" class="muted">No experiments loaded.</td></tr></tbody>
      </table>
    </div>
  </div>

  <div class="section card">
    <div class="label">System Health</div>
    <pre id="health">Loading...</pre>
    <button onclick="load()">Refresh</button>
    <button onclick="initDb()">Initialize Database</button>
  </div>
</main>
<script>
const money = v => (v===undefined||v===null)?'—':Number(v).toLocaleString(undefined,{maximumFractionDigits:2});

async function load(){
  const s=await (await fetch('/api/status')).json();
  mode.textContent=s.trading_mode.toUpperCase();
  live.textContent=s.live_trading_enabled?'ENABLED':'DISABLED';
  live.className='value '+(s.live_trading_enabled?'bad':'ok');
  mt5.textContent=s.mt5.terminal_connected?'CONNECTED':'OFFLINE';
  mt5.className='value '+(s.mt5.terminal_connected?'ok':'warn');
  symbol.textContent=s.symbol;
  risk.textContent=JSON.stringify(s.risk_policy,null,2);
  health.textContent=JSON.stringify(s.mt5,null,2);

  const a=await (await fetch('/api/mt5/account')).json();
  if(a.available){
    balance.textContent=(a.currency||'')+' '+money(a.balance);
    equity.textContent=(a.currency||'')+' '+money(a.equity);
  } else {
    balance.textContent='—';
    equity.textContent='—';
  }
}

async function loadDecision(){
  decisionStatus.textContent='CHECKING';
  decisionStatus.className='value warn';
  const d=await (await fetch('/api/decision')).json();
  decisionStatus.textContent=(d.status||'unknown').toUpperCase();
  decisionStatus.className='value '+(d.status==='candidate'?'ok':d.status==='blocked'?'bad':'warn');
  decisionReason.textContent=d.reason||'';
  decision.textContent=JSON.stringify(d,null,2);
}

async function runBacktest(){
  backtest.textContent='Running...';
  const b=await (await fetch('/api/backtest/mt5?h1_bars=2500&m15_bars=10000&cost_r=0.05')).json();
  backtest.textContent=JSON.stringify({
    available:b.available,
    source:b.source,
    metrics:b.metrics,
    parameters:b.parameters,
    assumptions:b.assumptions
  },null,2);
}

async function loadExperiments(){
  const r=await (await fetch('/api/research/experiments?limit=50')).json();
  research.textContent=r.ok?'Loaded '+r.experiments.length+' saved experiments.':JSON.stringify(r,null,2);
  const body=document.getElementById('experiments');
  if(!r.experiments||!r.experiments.length){
    body.innerHTML='<tr><td colspan="7" class="muted">No saved experiments yet.</td></tr>';
    return;
  }
  body.innerHTML=r.experiments.map(e=>{
    const m=e.metrics||{};
    return '<tr>'+
      '<td>'+new Date(e.created_at).toLocaleString()+'</td>'+
      '<td>'+e.strategy_version+'</td>'+
      '<td><span class="pill">'+e.stage+'</span></td>'+
      '<td>'+money(m.profit_factor)+'</td>'+
      '<td>'+money(m.expectancy_r)+'</td>'+
      '<td>'+money(e.score)+'</td>'+
      '<td><code>'+JSON.stringify(e.parameters)+'</code></td>'+
    '</tr>';
  }).join('');
}

async function initDb(){
  const r=await fetch('/api/database/init',{method:'POST'});
  const j=await r.json();
  health.textContent=JSON.stringify(j,null,2);
  if(j.ok) loadExperiments();
}

load();
loadExperiments();
</script>
</body>
</html>
"""
