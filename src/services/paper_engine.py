from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.config import Settings
from src.models.market import OrderBookSnapshot
from src.models.paper_trade import PaperTradeRequest, PaperTradeResult


class PaperEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def simulate(self, request: PaperTradeRequest, snapshot: OrderBookSnapshot, fee_enabled: bool) -> PaperTradeResult:
        now = datetime.now(timezone.utc)
        entry_price = snapshot.best_ask if request.entry_mode == "ask" else min(snapshot.best_ask, snapshot.best_bid + 0.01)

        target_price = min(0.95, entry_price * (1 + request.take_profit_pct))
        if snapshot.best_bid >= target_price:
            exit_price = snapshot.best_bid
            exit_reason = "take-profit"
        elif snapshot.top_depth < request.liquidity_stop_min_depth:
            exit_price = max(snapshot.best_bid - 0.01, 0.01)
            exit_reason = "liquidity-stop"
        else:
            exit_price = snapshot.best_bid
            exit_reason = "time-stop"

        qty = request.quantity
        gross_pnl = (exit_price - entry_price) * qty
        fee_rate = self.settings.fee_rate_bps / 10000 if fee_enabled else 0.0
        fees_paid = (entry_price * qty + exit_price * qty) * fee_rate
        net_pnl = gross_pnl - fees_paid

        return PaperTradeResult(
            market_id=request.market_id,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=qty,
            gross_pnl=gross_pnl,
            fees_paid=fees_paid,
            net_pnl=net_pnl,
            opened_at=now,
            closed_at=now + timedelta(hours=request.time_stop_hours),
            exit_reason=exit_reason,
        )
