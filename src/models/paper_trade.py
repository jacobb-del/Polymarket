from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class PaperTradeRequest:
    market_id: str
    side: str = "BUY"
    quantity: float = 100.0
    entry_mode: str = "ask"
    take_profit_pct: float = 0.5
    time_stop_hours: int = 24
    liquidity_stop_min_depth: float = 25.0


@dataclass(slots=True)
class PaperTradeResult:
    market_id: str
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    fees_paid: float
    net_pnl: float
    opened_at: datetime
    closed_at: datetime
    exit_reason: str
