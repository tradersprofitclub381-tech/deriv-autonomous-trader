"""
Instrument Discovery Engine
Dynamically discovers and classifies all supported synthetic indices.
"""

from typing import List, Dict
from loguru import logger

class InstrumentRegistry:
    def __init__(self):
        self.instruments: Dict[str, Dict] = {}
        self.families = {
            "volatility": [],
            "volatility_1s": [],
            "crash": [],
            "boom": [],
            "jump": [],
            "step": [],
            "range_break": [],
            "other": []
        }

    def classify_symbol(self, symbol_info: Dict) -> str:
        """Classify a symbol into its mathematical family based on name/code."""
        name = symbol_info.get("underlying_symbol_name", symbol_info.get("display_name", "")).lower()
        symbol = symbol_info.get("underlying_symbol", symbol_info.get("symbol", "")).upper()

        if "volatility" in name or symbol.startswith(("R_", "1HZ")):
            if "1s" in name or "1HZ" in symbol:
                return "volatility_1s"
            return "volatility"
        if "crash" in name or symbol.startswith("CRASH"):
            return "crash"
        if "boom" in name or symbol.startswith("BOOM"):
            return "boom"
        if "jump" in name:
            return "jump"
        if "step" in name:
            return "step"
        if "range break" in name or "rb" in symbol.lower():
            return "range_break"
        return "other"

    def load_from_api_response(self, active_symbols_response: Dict):
        """Populate registry from active_symbols API response."""
        symbols = active_symbols_response.get("active_symbols", [])
        for s in symbols:
            market = s.get("market", "")
            if market == "synthetic_index" or "synthetic" in str(s.get("market_display_name", "")).lower():
                symbol = s.get("underlying_symbol") or s.get("symbol")
                if not symbol:
                    continue
                family = self.classify_symbol(s)
                self.instruments[symbol] = {
                    **s,
                    "symbol": symbol,
                    "family": family,
                    "enabled": True
                }
                self.families[family].append(symbol)
        logger.info(f"Discovered {len(self.instruments)} synthetic instruments")
        for fam, syms in self.families.items():
            if syms:
                logger.info(f"  {fam}: {len(syms)} instruments")

    def get_by_family(self, family: str) -> List[str]:
        return self.families.get(family, [])

    def get_all_symbols(self) -> List[str]:
        return list(self.instruments.keys())
