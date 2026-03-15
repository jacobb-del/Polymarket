from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScoreBreakdown:
    market_id: str
    catalyst_score: float
    liquidity_score: float
    asymmetry_score: float
    movement_score: float
    friction_penalty: float
    total_score: float
    notes: list[str]


@dataclass(slots=True)
class CandidateRow:
    market_id: str
    event_id: str | None
    title: str
    slug: str
    best_bid: float
    best_ask: float
    spread: float
    top_depth: float
    fees_enabled: bool
    catalyst_hours: float | None
    score: ScoreBreakdown
