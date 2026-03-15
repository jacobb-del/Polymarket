from datetime import datetime, timezone

from src.config import Settings
from src.models.market import Market, OrderBookSnapshot
from src.services.market_filter import MarketFilter


def test_market_filters_tradable_and_liquid() -> None:
    settings = Settings()
    filt = MarketFilter(settings)

    markets = [
        Market("1", None, "A", "a", None, None, True, False, True, False, None, ["t1"]),
        Market("2", None, "B", "b", None, None, False, False, True, False, None, ["t2"]),
    ]
    tradable = filt.tradable_markets(markets)
    assert len(tradable) == 1

    snap = OrderBookSnapshot("1", "t1", 0.09, 0.10, 30, 35, 65, 0.01, datetime.now(timezone.utc))
    assert filt.price_window([snap])
    assert filt.liquid([snap])
