from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from src.config import Settings
from src.models.market import Market

logger = logging.getLogger(__name__)


class GammaClient:
    """Client for public Gamma discovery APIs."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_markets(self, limit: int = 200) -> list[Market]:
        url = f"{self.settings.gamma_base_url}/markets?{urlencode({'active': 'true', 'limit': limit})}"
        payload = self._fetch_json(url)

        if isinstance(payload, dict):
            items = payload.get("data") or payload.get("markets") or []
        else:
            items = payload

        markets: list[Market] = []
        for item in items:
            parsed = self._parse_market(item)
            if parsed:
                markets.append(parsed)
        logger.info("Fetched %s markets from Gamma", len(markets))
        return markets

    def _fetch_json(self, url: str) -> Any:
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                with urlopen(url, timeout=self.settings.request_timeout_seconds) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_exc = exc
                time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"Failed to fetch Gamma URL after retries: {url}") from last_exc

    def _parse_market(self, item: dict[str, Any]) -> Market | None:
        market_id = str(item.get("id") or item.get("marketId") or "")
        if not market_id:
            return None
        event_id = item.get("eventId") or item.get("event_id")
        title = item.get("question") or item.get("title") or "Untitled market"
        slug = item.get("slug") or market_id
        description = item.get("description")
        rules = item.get("rules") or item.get("resolutionSource")
        active = bool(item.get("active", True))
        closed = bool(item.get("closed", False))
        enable_order_book = bool(item.get("enableOrderBook", item.get("clobEnabled", False)))
        fees_enabled = bool(item.get("feesEnabled", False))
        end_date = _parse_dt(item.get("endDate") or item.get("end_date") or item.get("resolutionDate"))

        tokens = item.get("tokens") or item.get("outcomes") or []
        token_ids: list[str] = []
        for token in tokens:
            if isinstance(token, dict):
                token_id = token.get("token_id") or token.get("id") or token.get("tokenId")
                if token_id is not None:
                    token_ids.append(str(token_id))

        return Market(
            market_id=market_id,
            event_id=str(event_id) if event_id else None,
            title=title,
            slug=slug,
            description=description,
            rules=rules,
            active=active,
            closed=closed,
            enable_order_book=enable_order_book,
            fees_enabled=fees_enabled,
            end_date=end_date,
            token_ids=token_ids,
            raw=item,
        )


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
