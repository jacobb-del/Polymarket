from __future__ import annotations

import json
import logging

try:
    import websockets
except ModuleNotFoundError:  # pragma: no cover
    websockets = None

logger = logging.getLogger(__name__)


class WebsocketMarketStream:
    """Lightweight websocket listener for future near-real-time updates."""

    def __init__(self, url: str) -> None:
        self.url = url

    async def stream(self) -> None:
        if websockets is None:
            raise RuntimeError("websockets package is not installed")
        async with websockets.connect(self.url) as ws:
            logger.info("Connected websocket stream: %s", self.url)
            async for message in ws:
                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:
                    logger.debug("Non-JSON websocket payload ignored")
                    continue
                logger.info("Stream message: %s", payload)
