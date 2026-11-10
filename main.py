"""
Main entry point - Phase 1 demonstration
Discovers instruments and streams ticks from a public connection.
"""

import asyncio
from loguru import logger
from core.api_gateway import DerivAPIGateway
from core.instrument_registry import InstrumentRegistry

async def main():
    logger.info("Starting Deriv Autonomous Trading System - Phase 1 Foundation")

    gateway = DerivAPIGateway()
    registry = InstrumentRegistry()

    try:
        await gateway.connect_public()

        # Discover instruments
        symbols_response = await gateway.get_active_symbols()
        registry.load_from_api_response(symbols_response)

        logger.info(f"Total instruments discovered: {len(registry.get_all_symbols())}")

        # Example: subscribe to Volatility 100 if available
        vol100_symbols = [s for s in registry.get_all_symbols() if "100" in s and "R_" in s or "1HZ100" in s]
        if vol100_symbols:
            symbol = vol100_symbols[0]
            logger.info(f"Subscribing to ticks for {symbol}")

            def on_tick(data):
                tick = data.get("tick", {})
                logger.info(f"Tick {symbol}: {tick.get('quote')} @ {tick.get('epoch')}")

            await gateway.subscribe_ticks(symbol, on_tick)

            # Keep running for a short demonstration
            await asyncio.sleep(30)
        else:
            logger.warning("No Volatility 100 symbol found for demo subscription")

    except Exception as e:
        logger.exception(f"Error in main: {e}")
    finally:
        await gateway.close()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
