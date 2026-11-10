"""
Deriv API Gateway
Handles public market data and authenticated trading sessions.
Uses the modern OTP-based authentication flow + public WebSocket.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Callable
import websockets
from loguru import logger

PUBLIC_WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"
APP_ID = 1089  # Default testing app_id; replace with your own registered app

class DerivAPIGateway:
    def __init__(self, app_id: int = APP_ID):
        self.app_id = app_id
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.subscriptions: Dict[str, Callable] = {}
        self.req_id_counter = 1
        self.pending_requests: Dict[int, asyncio.Future] = {}

    async def connect_public(self):
        """Connect to public market data endpoint (no authentication required)."""
        url = f"{PUBLIC_WS_URL}?app_id={self.app_id}"
        try:
            self.ws = await websockets.connect(url, ping_interval=30, ping_timeout=10)
            self.connected = True
            logger.info("Connected to Deriv public WebSocket")
            asyncio.create_task(self._listen())
        except Exception as e:
            logger.error(f"Public connection failed: {e}")
            raise

    async def _listen(self):
        """Background listener for incoming messages."""
        try:
            async for message in self.ws:
                data = json.loads(message)
                req_id = data.get("req_id")
                if req_id and req_id in self.pending_requests:
                    future = self.pending_requests.pop(req_id)
                    if not future.done():
                        future.set_result(data)
                msg_type = data.get("msg_type")
                if msg_type in self.subscriptions:
                    self.subscriptions[msg_type](data)
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            logger.warning("WebSocket connection closed")

    async def send_request(self, payload: Dict[str, Any], timeout: float = 10.0) -> Dict[str, Any]:
        """Send a request and wait for the matching response."""
        if not self.connected or not self.ws:
            raise RuntimeError("Not connected")
        req_id = self.req_id_counter
        self.req_id_counter += 1
        payload["req_id"] = req_id
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[req_id] = future
        await self.ws.send(json.dumps(payload))
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            self.pending_requests.pop(req_id, None)
            raise TimeoutError(f"Request {req_id} timed out")

    async def get_active_symbols(self) -> Dict[str, Any]:
        """Retrieve all active symbols (including synthetic indices)."""
        return await self.send_request({
            "active_symbols": "full"
        })

    async def subscribe_ticks(self, symbol: str, callback: Callable):
        """Subscribe to real-time ticks for a symbol."""
        self.subscriptions["tick"] = callback
        await self.ws.send(json.dumps({
            "ticks": symbol,
            "subscribe": 1,
            "req_id": self.req_id_counter
        }))
        self.req_id_counter += 1

    async def get_ticks_history(self, symbol: str, count: int = 5000, style: str = "ticks") -> Dict[str, Any]:
        """Fetch historical ticks."""
        return await self.send_request({
            "ticks_history": symbol,
            "count": count,
            "end": "latest",
            "style": style
        })

    async def get_contracts_for(self, symbol: str, currency: str = "USD") -> Dict[str, Any]:
        """Discover available contracts for a symbol."""
        return await self.send_request({
            "contracts_for": symbol,
            "currency": currency,
            "product_type": "basic"
        })

    async def close(self):
        if self.ws:
            await self.ws.close()
            self.connected = False
