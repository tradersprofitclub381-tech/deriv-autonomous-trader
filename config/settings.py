# Independent Risk Configuration and Operational Constants

RISK_CONFIG = {
    "base_stake_pct": 0.0025,
    "max_aggregate_exposure_pct": 0.01,
    "daily_loss_limit_pct": 0.02,
    "consecutive_loss_breaker": 3,
}

# These thresholds must be validated empirically per instrument
HURST_TREND_THRESHOLD = 0.52
HURST_MEAN_REVERSION_THRESHOLD = 0.50
