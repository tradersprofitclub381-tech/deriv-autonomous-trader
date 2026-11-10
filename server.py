"""
Server entry point.
Run this to start the control dashboard and autonomous loop.
"""

from dashboard.app import run_server

if __name__ == "__main__":
    print("=" * 60)
    print("DERIV AUTONOMOUS TRADER SERVER")
    print("Dashboard: http://localhost:5000")
    print("Controls: START / PAUSE / RESUME / EMERGENCY STOP")
    print("Enter API token on the dashboard to begin.")
    print("Demo mode strongly recommended. Risk Manager has absolute authority.")
    print("=" * 60)
    run_server(host="0.0.0.0", port=5000)
