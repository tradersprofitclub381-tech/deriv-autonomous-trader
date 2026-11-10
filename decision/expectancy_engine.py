"""
Mathematical Expectancy Engine
Calculates payout-adjusted expected value and break-even probability.
"""

from typing import Dict

class ExpectancyEngine:
    @staticmethod
    def calculate(stake: float, net_payout_ratio: float, win_probability: float) -> Dict:
        """
        EV = p * R - (1 - p)
        where R is net profit per unit stake.
        """
        R = net_payout_ratio
        p = win_probability
        ev_per_unit = p * R - (1 - p)
        ev = stake * ev_per_unit
        break_even_p = 1 / (1 + R) if R > -1 else 1.0

        return {
            "expected_value": ev,
            "ev_per_unit": ev_per_unit,
            "break_even_probability": break_even_p,
            "win_probability": p,
            "net_payout_ratio": R,
            "eligible": p > break_even_p and ev > 0
        }
