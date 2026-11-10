# Deriv Autonomous Quantitative Trading System

**Status:** Server mode + Phase 1–4 skeleton

## Quick Start

```bash
git clone https://github.com/tradersprofitclub381-tech/deriv-autonomous-trader.git
cd deriv-autonomous-trader
pip install -r requirements.txt
python server.py
```

Open **http://localhost:5000**

### Master Controls
- Enter your **API Token** (demo strongly recommended)
- Select Demo or Real
- **START AUTONOMOUS TRADING** — enables the loop (scans, evaluates, only trades on positive EV + risk approval)
- **PAUSE NEW TRADES**
- **RESUME TRADING**
- **EMERGENCY STOP** — immediate halt (Risk Manager absolute authority)

The system stays selective. It will not force trades. Full strategy library, calibrated probability models, and authenticated execution are wired as skeletons and activate only after validation.

## Architecture Modules Present
- API Gateway (public + authenticated-ready)
- Instrument Registry (dynamic discovery)
- Independent Risk Manager (veto power)
- Expectancy Engine
- Execution Engine (proposal → validate → buy → monitor path)
- Control Dashboard (Flask) with API token input

## Safety
- Demo first. Real account only after full out-of-sample validation
- No martingale / stake increase after loss
- Token used only in memory for the session. Never logged or stored in files
- Credentials via environment variables or dashboard input only

## Next
Authenticated trading path (OTP), regime detectors, strategy library, probability calibration, SQLite journal, and rigorous backtester.
