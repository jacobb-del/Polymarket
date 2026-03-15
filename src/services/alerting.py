from __future__ import annotations

import json
import logging
from pathlib import Path

try:
    from tabulate import tabulate
except ModuleNotFoundError:  # pragma: no cover
    def tabulate(rows, headers):
        lines=[" | ".join(headers)]
        for r in rows:
            lines.append(" | ".join(str(x) for x in r))
        return "\n".join(lines)

from src.models.score import CandidateRow

logger = logging.getLogger(__name__)


class AlertingService:
    def __init__(self, alert_threshold: float) -> None:
        self.alert_threshold = alert_threshold

    def render_table(self, candidates: list[CandidateRow]) -> str:
        rows = [
            [
                c.market_id,
                c.title[:42],
                f"{c.best_bid:.3f}",
                f"{c.best_ask:.3f}",
                f"{c.spread:.3f}",
                f"{c.top_depth:.1f}",
                "Y" if c.fees_enabled else "N",
                f"{c.score.total_score:.3f}",
            ]
            for c in candidates
        ]
        return tabulate(rows, headers=["market", "title", "bid", "ask", "spread", "depth", "fees", "score"])

    def print_alerts(self, candidates: list[CandidateRow]) -> None:
        for c in candidates:
            if c.score.total_score >= self.alert_threshold:
                logger.warning("ALERT %s (%s): score %.3f", c.title, c.market_id, c.score.total_score)

    def save_json(self, candidates: list[CandidateRow], output_path: str) -> None:
        payload = [
            {
                "market_id": c.market_id,
                "event_id": c.event_id,
                "title": c.title,
                "slug": c.slug,
                "best_bid": c.best_bid,
                "best_ask": c.best_ask,
                "spread": c.spread,
                "top_depth": c.top_depth,
                "fees_enabled": c.fees_enabled,
                "catalyst_hours": c.catalyst_hours,
                "score": {
                    "total": c.score.total_score,
                    "catalyst": c.score.catalyst_score,
                    "liquidity": c.score.liquidity_score,
                    "asymmetry": c.score.asymmetry_score,
                    "movement": c.score.movement_score,
                    "friction_penalty": c.score.friction_penalty,
                    "notes": c.score.notes,
                },
            }
            for c in candidates
        ]
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2))
