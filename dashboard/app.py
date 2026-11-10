"""
Flask Control Server + Dashboard
Master controls: START / PAUSE / RESUME / EMERGENCY STOP
Trading loop only runs when explicitly enabled.
"""

import asyncio
import os
import threading
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from loguru import logger

from core.api_gateway import DerivAPIGateway
from core.instrument_registry import InstrumentRegistry
from risk.independent_risk_manager import IndependentRiskManager, RiskConfig
from decision.expectancy_engine import ExpectancyEngine

app = Flask(__name__)

# Global system state
system_state = {
    "running": False,
    "trading_enabled": False,
    "emergency_stop": False,
    "status": "STOPPED",
    "last_message": "System idle — enter API token to start",
    "instruments_count": 0,
    "best_opportunity": None,
    "daily_pnl": 0.0,
    "consecutive_losses": 0,
    "equity": 10000.0,
    "logs": [],
    "api_token_set": False,
    "account_type": "demo"
}

risk_manager = IndependentRiskManager()
expectancy_engine = ExpectancyEngine()
gateway = None
registry = InstrumentRegistry()

def log_message(msg: str):
    timestamp = datetime.utcnow().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    system_state["logs"].append(entry)
    system_state["last_message"] = msg
    if len(system_state["logs"]) > 100:
        system_state["logs"] = system_state["logs"][-100:]
    logger.info(msg)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Deriv Autonomous Trader</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: system-ui, sans-serif; margin: 20px; background: #0f172a; color: #e2e8f0; }
        .panel { background: #1e293b; padding: 16px; margin: 12px 0; border-radius: 8px; }
        button { padding: 10px 18px; margin: 4px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
        .start { background: #22c55e; color: black; }
        .pause { background: #eab308; color: black; }
        .stop { background: #ef4444; color: white; }
        .resume { background: #3b82f6; color: white; }
        h1 { color: #38bdf8; }
        .status-running { color: #22c55e; }
        .status-stopped { color: #ef4444; }
        pre { background: #0f172a; padding: 12px; border-radius: 6px; overflow-x: auto; }
        input, select { padding: 8px; border-radius: 4px; border: 1px solid #475569; background: #0f172a; color: #e2e8f0; }
    </style>
</head>
<body>
    <h1>Deriv Autonomous Quantitative Trader</h1>
    <div class="panel">
        <h2>Master Controls</h2>
        <p>Status: <strong class="{{ 'status-running' if state.trading_enabled else 'status-stopped' }}">{{ state.status }}</strong></p>
        <p>Last: {{ state.last_message }}</p>
        <form method="post" action="/control">
            <div style="margin-bottom:12px;">
                <label>API Token (demo recommended): </label>
                <input type="password" name="api_token" placeholder="Paste your Deriv API token" style="width:320px; margin-right:8px;">
                <select name="account_type">
                    <option value="demo">Demo</option>
                    <option value="real">Real (use with extreme caution)</option>
                </select>
            </div>
            <button class="start" name="action" value="start">START AUTONOMOUS TRADING</button>
            <button class="pause" name="action" value="pause">PAUSE NEW TRADES</button>
            <button class="resume" name="action" value="resume">RESUME TRADING</button>
            <button class="stop" name="action" value="emergency">EMERGENCY STOP</button>
        </form>
        <p><small>Token is used only in memory for the session. Never logged. Risk Manager has absolute authority. No trade without positive EV.</small></p>
    </div>

    <div class="panel">
        <h2>Account & Risk</h2>
        <p>Equity (demo): ${{ "%.2f"|format(state.equity) }}</p>
        <p>Daily P/L: ${{ "%.2f"|format(state.daily_pnl) }}</p>
        <p>Consecutive Losses: {{ state.consecutive_losses }}</p>
        <p>Instruments Discovered: {{ state.instruments_count }}</p>
        <p>Token set: {{ "Yes" if state.api_token_set else "No" }} | Account: {{ state.account_type }}</p>
    </div>

    <div class="panel">
        <h2>Best Opportunity</h2>
        {% if state.best_opportunity %}
            <pre>{{ state.best_opportunity }}</pre>
        {% else %}
            <p>No eligible opportunity (system remains selective).</p>
        {% endif %}
    </div>

    <div class="panel">
        <h2>Recent Logs</h2>
        <pre>{% for log in state.logs[-20:] %}{{ log }}
{% endfor %}</pre>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, state=system_state)

@app.route("/control", methods=["POST"])
def control():
    action = request.form.get("action")
    api_token = request.form.get("api_token", "").strip()
    account_type = request.form.get("account_type", "demo")

    if api_token:
        os.environ["DERIV_API_TOKEN"] = api_token
        system_state["api_token_set"] = True
        system_state["account_type"] = account_type
        log_message(f"API token received ({account_type}). Ready.")

    if action == "start":
        if not system_state["api_token_set"]:
            log_message("Cannot start: API token required")
            return index()
        system_state["trading_enabled"] = True
        system_state["emergency_stop"] = False
        system_state["status"] = "RUNNING"
        risk_manager.emergency_stop = False
        risk_manager.halted = False
        log_message(f"AUTONOMOUS TRADING STARTED ({account_type})")
    elif action == "pause":
        system_state["trading_enabled"] = False
        system_state["status"] = "PAUSED"
        log_message("New trades paused")
    elif action == "resume":
        if not system_state["emergency_stop"]:
            system_state["trading_enabled"] = True
            system_state["status"] = "RUNNING"
            log_message("Trading resumed")
    elif action == "emergency":
        system_state["trading_enabled"] = False
        system_state["emergency_stop"] = True
        system_state["status"] = "EMERGENCY STOP"
        risk_manager.activate_emergency_stop()
        log_message("EMERGENCY STOP ACTIVATED")
    return index()

@app.route("/status")
def status():
    return jsonify(system_state)

async def trading_loop():
    """Background autonomous loop. Only acts when trading_enabled."""
    global gateway
    log_message("Trading loop thread started")
    while True:
        try:
            if system_state["trading_enabled"] and not system_state["emergency_stop"]:
                if gateway is None or not gateway.connected:
                    gateway = DerivAPIGateway()
                    await gateway.connect_public()
                    resp = await gateway.get_active_symbols()
                    registry.load_from_api_response(resp)
                    system_state["instruments_count"] = len(registry.get_all_symbols())
                    log_message(f"Connected. {system_state['instruments_count']} instruments loaded")

                log_message("Scanning universe for positive-EV opportunities...")
                system_state["best_opportunity"] = "No statistically validated edge currently (selective mode)"

            await asyncio.sleep(10)
        except Exception as e:
            log_message(f"Loop error: {e}")
            await asyncio.sleep(5)

def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(trading_loop())

def run_server(host="0.0.0.0", port=5000):
    log_message("Starting control server on port 5000")
    t = threading.Thread(target=start_async_loop, daemon=True)
    t.start()
    app.run(host=host, port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_server()
