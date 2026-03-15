from __future__ import annotations

import logging

from src.clients.polymarket_gamma import GammaClient
from src.models.market import Market

logger = logging.getLogger(__name__)


class MarketLoader:
    def __init__(self, gamma_client: GammaClient) -> None:
        self.gamma_client = gamma_client

    def load_active_markets(self) -> list[Market]:
        markets = self.gamma_client.fetch_markets()
        logger.info("Loaded %s active markets", len(markets))
        return markets
