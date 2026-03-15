from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Market:
    market_id: str
    event_id: str | None
    title: str
    slug: str
    description: str | None
    rules: str | None
    active: bool
    closed: bool
    enable_order_book: bool
    fees_enabled: bool
    end_date: datetime | None
    token_ids: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class OrderBookSnapshot:
    market_id: str
    token_id: str | None
    best_bid: float
    best_ask: float
    bid_size: float
    ask_size: float
    top_depth: float
    spread: float
    timestamp: datetime


@dataclass(slots=True)
class TradeTick:
    market_id: str
    token_id: str | None
    price: float
    size: float
    side: str
    timestamp: datetime
