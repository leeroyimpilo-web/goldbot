DASHBOARD_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>GoldBot AI</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,sans-serif}
body{margin:0;background:#080b10;color:#edf2f7}
header{padding:24px 28px;border-bottom:1px solid #202733;background:#0d1117}
h1{margin:0;font-size:24px}.sub{color:#8b98a8;margin-top:4px}
main{padding:24px;max-width:1200px;margin:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.card{background:#10161f;border:1px solid #232d3a;border-radius:16px;padding:18px}
.label{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:#8592a3}
.value{font-size:25px;margin-top:8px;font-weight:700}
.ok{color:#66e3a4}.warn{color:#ffd166}.bad{color:#ff6b6b}
.section{margin-top:18px}
pre{white-space:pre-wrap;color:#b9c5d3;font-size:12px}
button{background:#1b2636;color:white;border:1px solid #34445a;border-radius:10px;padding:10px 14px;cursor:pointer}
</style>
</head>
<body>
<header><h1>GoldBot AI</h1><div class="sub">Research-first XAUUSD trading control centre</div></header>
<main>
<div class="grid">
<div class="card"><div class="label">Trading Mode</div><div id="mode" class="value warn">...</div></div>
<div class="card"><div class="label">Live Orders</div><div id="live" class="value">...</div></div>
<div class="card"><div class="label">MT5</div><div id="mt5" class="value">...</div></div>
<div class="card"><div class="label">Symbol</div><div id="symbol" class="value">XAUUSD</div></div>
</div>
<div class="section grid">
<div class="card"><div class="label">Strategy</div><div class="value">MTF Breakout v1</div><p>H1 regime → M15 breakout → ATR risk gates.</p></div>
<div class="card"><div class="label">Risk Policy</div><pre id="risk">Loading...</pre></div>
</div>
<div class="section card"><div class="label">System Health</div><pre id="health">Loading...</pre><button onclick="load()">Refresh</button></div>
</main>
<script>
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
}
load();
</script>
</body>
</html>
"""
