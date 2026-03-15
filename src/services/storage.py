from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone

from src.models.paper_trade import PaperTradeResult
from src.models.score import CandidateRow


class Storage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def init(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scanned_at TEXT NOT NULL,
                    market_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    best_bid REAL NOT NULL,
                    best_ask REAL NOT NULL,
                    spread REAL NOT NULL,
                    top_depth REAL NOT NULL,
                    fees_enabled INTEGER NOT NULL,
                    catalyst_hours REAL,
                    total_score REAL NOT NULL,
                    breakdown_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    closed_at TEXT NOT NULL,
                    market_id TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    gross_pnl REAL NOT NULL,
                    fees_paid REAL NOT NULL,
                    net_pnl REAL NOT NULL,
                    exit_reason TEXT NOT NULL
                )
                """
            )

    def persist_candidates(self, candidates: list[CandidateRow]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """
                INSERT INTO scan_candidates (
                    scanned_at, market_id, title, slug, best_bid, best_ask, spread,
                    top_depth, fees_enabled, catalyst_hours, total_score, breakdown_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        now,
                        c.market_id,
                        c.title,
                        c.slug,
                        c.best_bid,
                        c.best_ask,
                        c.spread,
                        c.top_depth,
                        int(c.fees_enabled),
                        c.catalyst_hours,
                        c.score.total_score,
                        str(asdict(c.score)),
                    )
                    for c in candidates
                ],
            )

    def persist_paper_trade(self, trade: PaperTradeResult) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO paper_trades (
                    closed_at, market_id, entry_price, exit_price, quantity,
                    gross_pnl, fees_paid, net_pnl, exit_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade.closed_at.isoformat(),
                    trade.market_id,
                    trade.entry_price,
                    trade.exit_price,
                    trade.quantity,
                    trade.gross_pnl,
                    trade.fees_paid,
                    trade.net_pnl,
                    trade.exit_reason,
                ),
            )
