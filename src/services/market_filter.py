from __future__ import annotations

from datetime import datetime, timezone

from src.config import Settings
from src.models.market import Market, OrderBookSnapshot


class MarketFilter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def tradable_markets(self, markets: list[Market]) -> list[Market]:
        return [m for m in markets if m.active and not m.closed and m.enable_order_book]

    def price_window(self, snapshots: list[OrderBookSnapshot]) -> list[OrderBookSnapshot]:
        result: list[OrderBookSnapshot] = []
        for snap in snapshots:
            if self.settings.min_price <= snap.best_ask <= self.settings.max_price:
                result.append(snap)
        return result

    def liquid(self, snapshots: list[OrderBookSnapshot]) -> list[OrderBookSnapshot]:
        return [
            s
            for s in snapshots
            if s.top_depth >= self.settings.min_top_book_depth and s.spread <= self.settings.max_spread
        ]

    def catalyst_window_ok(self, catalyst_dt: datetime | None) -> bool:
        if catalyst_dt is None:
            return False
        now = datetime.now(timezone.utc)
        if catalyst_dt.tzinfo is None:
            catalyst_dt = catalyst_dt.replace(tzinfo=timezone.utc)
        delta_hours = (catalyst_dt - now).total_seconds() / 3600
        return self.settings.catalyst_min_hours <= delta_hours <= self.settings.catalyst_max_days * 24
