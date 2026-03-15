from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from src.config import Settings
from src.models.market import OrderBookSnapshot


class ClobClient:
    """Minimal CLOB client using public endpoints."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_orderbook(self, token_id: str, market_id: str) -> OrderBookSnapshot:
        url = f"{self.settings.clob_base_url}/book?{urlencode({'token_id': token_id})}"
        payload = self._fetch_json(url)

        bids = payload.get("bids", [])
        asks = payload.get("asks", [])

        best_bid, bid_size = _best_px_and_size(bids, reverse=True)
        best_ask, ask_size = _best_px_and_size(asks, reverse=False)

        spread = max(best_ask - best_bid, 0.0) if best_ask > 0 and best_bid > 0 else 1.0
        top_depth = bid_size + ask_size
        return OrderBookSnapshot(
            market_id=market_id,
            token_id=token_id,
            best_bid=best_bid,
            best_ask=best_ask,
            bid_size=bid_size,
            ask_size=ask_size,
            top_depth=top_depth,
            spread=spread,
            timestamp=datetime.now(timezone.utc),
        )

    def _fetch_json(self, url: str) -> Any:
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                with urlopen(url, timeout=self.settings.request_timeout_seconds) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_exc = exc
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"Failed to fetch CLOB URL after retries: {url}") from last_exc


def _best_px_and_size(levels: list[dict], reverse: bool) -> tuple[float, float]:
    if not levels:
        return 0.0, 0.0
    parsed: list[tuple[float, float]] = []
    for level in levels:
        price = float(level.get("price", 0))
        size = float(level.get("size") or level.get("amount") or 0)
        parsed.append((price, size))

    parsed.sort(key=lambda x: x[0], reverse=reverse)
    return parsed[0]
