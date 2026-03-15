from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

from src.config import Settings
from src.models.market import Market, OrderBookSnapshot
from src.models.score import CandidateRow, ScoreBreakdown


@dataclass(slots=True)
class CatalystTag:
    slug_contains: str
    catalyst_datetime: datetime
    catalyst_type: str
    confidence: float


class Scorer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def load_manual_catalysts(self, file_path: str) -> list[CatalystTag]:
        path = Path(file_path)
        if not path.exists():
            return []
        if yaml is None:
            return []
        data = yaml.safe_load(path.read_text()) or {}
        rows = data.get("catalysts", [])
        tags: list[CatalystTag] = []
        for row in rows:
            dt = datetime.fromisoformat(str(row["catalyst_datetime"]).replace("Z", "+00:00"))
            tags.append(
                CatalystTag(
                    slug_contains=row["slug_contains"],
                    catalyst_datetime=dt,
                    catalyst_type=row.get("catalyst_type", "manual"),
                    confidence=float(row.get("confidence", 0.5)),
                )
            )
        return tags

    def score_market(
        self,
        market: Market,
        snapshot: OrderBookSnapshot,
        catalyst_dt: datetime | None,
        catalyst_confidence: float,
    ) -> CandidateRow:
        catalyst_score, catalyst_hours = self._catalyst_score(catalyst_dt, catalyst_confidence)
        liquidity_score = self._liquidity_score(snapshot)
        asymmetry_score = self._asymmetry_score(snapshot)
        movement_score = self._movement_score(market)
        friction_penalty = self._friction_penalty(market, snapshot)

        total_score = (
            catalyst_score * self.settings.weight_catalyst
            + liquidity_score * self.settings.weight_liquidity
            + asymmetry_score * self.settings.weight_asymmetry
            + movement_score * self.settings.weight_movement
            - friction_penalty
        )

        breakdown = ScoreBreakdown(
            market_id=market.market_id,
            catalyst_score=round(catalyst_score, 4),
            liquidity_score=round(liquidity_score, 4),
            asymmetry_score=round(asymmetry_score, 4),
            movement_score=round(movement_score, 4),
            friction_penalty=round(friction_penalty, 4),
            total_score=round(max(0.0, min(1.0, total_score)), 4),
            notes=self._build_notes(market, snapshot),
        )

        return CandidateRow(
            market_id=market.market_id,
            event_id=market.event_id,
            title=market.title,
            slug=market.slug,
            best_bid=snapshot.best_bid,
            best_ask=snapshot.best_ask,
            spread=snapshot.spread,
            top_depth=snapshot.top_depth,
            fees_enabled=market.fees_enabled,
            catalyst_hours=catalyst_hours,
            score=breakdown,
        )

    def resolve_catalyst(self, market: Market, manual: list[CatalystTag]) -> tuple[datetime | None, float]:
        for tag in manual:
            if tag.slug_contains.lower() in market.slug.lower() or tag.slug_contains.lower() in market.title.lower():
                return tag.catalyst_datetime, tag.confidence
        return market.end_date, 0.35

    def _catalyst_score(self, catalyst_dt: datetime | None, confidence: float) -> tuple[float, float | None]:
        if catalyst_dt is None:
            return 0.1 * confidence, None
        now = datetime.now(timezone.utc)
        if catalyst_dt.tzinfo is None:
            catalyst_dt = catalyst_dt.replace(tzinfo=timezone.utc)
        hours = (catalyst_dt - now).total_seconds() / 3600
        if hours <= 0:
            proximity = 0.0
        elif hours < 24:
            proximity = 1.0
        elif hours < 72:
            proximity = 0.8
        elif hours < 240:
            proximity = 0.6
        else:
            proximity = 0.3
        return min(1.0, max(0.0, proximity * confidence)), hours

    def _liquidity_score(self, snapshot: OrderBookSnapshot) -> float:
        spread_score = max(0.0, 1 - (snapshot.spread / max(self.settings.max_spread, 0.0001)))
        depth_score = min(1.0, snapshot.top_depth / (self.settings.min_top_book_depth * 4))
        return (spread_score * 0.6) + (depth_score * 0.4)

    def _asymmetry_score(self, snapshot: OrderBookSnapshot) -> float:
        price = snapshot.best_ask
        if price <= 0:
            return 0.0
        upside = (0.30 - price) / price
        normalized_upside = min(1.0, max(0.0, upside / 5))
        low_price_bonus = 1 - min(price / self.settings.max_price, 1.0)
        return normalized_upside * 0.7 + low_price_bonus * 0.3

    def _movement_score(self, market: Market) -> float:
        text = f"{market.title} {market.description or ''}".lower()
        hot_terms = ["debate", "vote", "hearing", "earnings", "deadline", "court", "cpi", "fed", "announcement"]
        hits = sum(1 for t in hot_terms if t in text)
        return min(1.0, 0.2 + hits * 0.12)

    def _friction_penalty(self, market: Market, snapshot: OrderBookSnapshot) -> float:
        penalty = 0.0
        if market.fees_enabled:
            penalty += 0.08
        if snapshot.spread > self.settings.max_spread:
            penalty += 0.08
        if snapshot.top_depth < self.settings.min_top_book_depth:
            penalty += 0.07
        if not market.rules:
            penalty += 0.03
        return penalty

    def _build_notes(self, market: Market, snapshot: OrderBookSnapshot) -> list[str]:
        notes = []
        if market.fees_enabled:
            notes.append("fee-enabled")
        if snapshot.top_depth < self.settings.min_top_book_depth:
            notes.append("thin-depth")
        if snapshot.spread > self.settings.max_spread:
            notes.append("wide-spread")
        return notes
