from datetime import datetime, timedelta, timezone

from src.config import Settings
from src.models.market import Market, OrderBookSnapshot
from src.services.scorer import Scorer


def test_scoring_returns_expected_range() -> None:
    settings = Settings()
    scorer = Scorer(settings)

    market = Market("1", "e1", "Fed announcement soon", "fed-event", "desc", "rules", True, False, True, False, None, ["tok"])
    snap = OrderBookSnapshot("1", "tok", 0.09, 0.1, 50, 60, 110, 0.01, datetime.now(timezone.utc))
    catalyst = datetime.now(timezone.utc) + timedelta(hours=12)

    result = scorer.score_market(market, snap, catalyst, 0.9)
    assert 0 <= result.score.total_score <= 1
    assert result.score.catalyst_score > 0
