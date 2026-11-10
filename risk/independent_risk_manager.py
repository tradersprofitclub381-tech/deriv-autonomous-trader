"""
Independent Risk Management Engine
Absolute authority. Never overridden by the AI analysis engine.
"""

from dataclasses import dataclass
from typing import Optional
from loguru import logger

@dataclass
class RiskConfig:
    base_stake_pct: float = 0.0025          # 0.25% of equity
    max_aggregate_exposure_pct: float = 0.01  # 1.00%
    daily_loss_limit_pct: float = 0.02      # 2.00%
    consecutive_loss_breaker: int = 3
    max_trades_per_cycle: int = 20
    daily_profit_target_pct: Optional[float] = None

class IndependentRiskManager:
    def __init__(self, config: RiskConfig = None):
        self.config = config or RiskConfig()
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.current_exposure = 0.0
        self.trades_today = 0
        self.halted = False
        self.emergency_stop = False

    def reset_daily(self, equity: float):
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.trades_today = 0
        self.current_exposure = 0.0
        self.halted = False

    def evaluate_trade(self, equity: float, proposed_stake: float, expected_value: float) -> tuple[bool, str, float]:
        """
        Returns: (approved, reason, approved_stake)
        """
        if self.emergency_stop or self.halted:
            return False, "System halted", 0.0

        if expected_value <= 0:
            return False, "Non-positive expected value", 0.0

        if self.consecutive_losses >= self.config.consecutive_loss_breaker:
            self.halted = True
            return False, "Consecutive loss breaker activated", 0.0

        if self.daily_pnl <= -equity * self.config.daily_loss_limit_pct:
            self.halted = True
            return False, "Daily loss limit reached", 0.0

        max_stake = equity * self.config.base_stake_pct
        if proposed_stake > max_stake:
            proposed_stake = max_stake

        if self.current_exposure + proposed_stake > equity * self.config.max_aggregate_exposure_pct:
            return False, "Aggregate exposure limit exceeded", 0.0

        if self.trades_today >= self.config.max_trades_per_cycle:
            return False, "Max trades per cycle reached", 0.0

        return True, "Approved", proposed_stake

    def record_result(self, pnl: float, stake: float):
        self.daily_pnl += pnl
        self.current_exposure = max(0, self.current_exposure - stake)
        self.trades_today += 1
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

    def activate_emergency_stop(self):
        self.emergency_stop = True
        self.halted = True
        logger.critical("EMERGENCY STOP ACTIVATED")
