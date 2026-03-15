from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from src.clients.polymarket_clob import ClobClient
from src.clients.polymarket_gamma import GammaClient
from src.clients.websocket_client import WebsocketMarketStream
from src.config import ensure_data_dir, load_settings
from src.models.paper_trade import PaperTradeRequest
from src.models.score import CandidateRow
from src.services.alerting import AlertingService
from src.services.market_filter import MarketFilter
from src.services.market_loader import MarketLoader
from src.services.paper_engine import PaperEngine
from src.services.scorer import Scorer
from src.services.storage import Storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


def run_scan(output_json: str = "data/shortlist.json", catalysts_file: str = "catalysts.yaml") -> list[CandidateRow]:
    settings = load_settings()
    ensure_data_dir(settings)

    gamma = GammaClient(settings)
    clob = ClobClient(settings)
    loader = MarketLoader(gamma)
    filt = MarketFilter(settings)
    scorer = Scorer(settings)
    alerts = AlertingService(settings.alert_score_threshold)
    storage = Storage(settings.db_path)
    storage.init()

    manual_catalysts = scorer.load_manual_catalysts(catalysts_file)

    try:
        markets = filt.tradable_markets(loader.load_active_markets())
    except Exception as exc:
        logger.error("Market discovery failed: %s", exc)
        markets = []

    scored: list[CandidateRow] = []
    for market in markets:
        if not market.token_ids:
            continue
        try:
            snap = clob.fetch_orderbook(token_id=market.token_ids[0], market_id=market.market_id)
        except Exception as exc:
            logger.warning("Skipping market %s due to orderbook error: %s", market.market_id, exc)
            continue

        if not filt.price_window([snap]):
            continue
        if not filt.liquid([snap]):
            continue

        catalyst_dt, confidence = scorer.resolve_catalyst(market, manual_catalysts)
        candidate = scorer.score_market(market, snap, catalyst_dt, confidence)
        scored.append(candidate)

    ranked = sorted(scored, key=lambda c: c.score.total_score, reverse=True)[: settings.top_n]
    storage.persist_candidates(ranked)

    print(alerts.render_table(ranked))
    alerts.save_json(ranked, output_json)
    alerts.print_alerts(ranked)
    logger.info("Saved %s candidates to %s", len(ranked), output_json)
    return ranked


def run_shortlist(limit: int = 10) -> None:
    ranked = run_scan()
    for row in ranked[:limit]:
        print(f"{row.market_id} | {row.score.total_score:.3f} | {row.title}")


def run_paper_trade(market_id: str) -> None:
    settings = load_settings()
    ensure_data_dir(settings)

    gamma = GammaClient(settings)
    clob = ClobClient(settings)
    storage = Storage(settings.db_path)
    storage.init()

    market = next((m for m in gamma.fetch_markets(limit=400) if m.market_id == market_id), None)
    if market is None or not market.token_ids:
        raise ValueError(f"Market {market_id} not found or no token IDs available")

    snapshot = clob.fetch_orderbook(market.token_ids[0], market.market_id)
    engine = PaperEngine(settings)
    result = engine.simulate(PaperTradeRequest(market_id=market_id), snapshot, fee_enabled=market.fees_enabled)
    storage.persist_paper_trade(result)
    print(result)


def run_stream() -> None:
    settings = load_settings()
    ws = WebsocketMarketStream(f"{settings.clob_base_url.replace('https', 'wss')}/ws")
    asyncio.run(ws.stream())


def run_backfill() -> None:
    out = Path("data/backfill_shortlist.json")
    run_scan(output_json=str(out))


def main() -> None:
    parser = argparse.ArgumentParser(description="Polymarket pre-resolution repricing scanner")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan")
    sub.add_parser("stream")
    sub.add_parser("shortlist")
    paper = sub.add_parser("paper-trade")
    paper.add_argument("--market", required=True)
    sub.add_parser("backfill")

    args = parser.parse_args()

    if args.command == "scan":
        run_scan()
    elif args.command == "stream":
        run_stream()
    elif args.command == "shortlist":
        run_shortlist()
    elif args.command == "paper-trade":
        run_paper_trade(args.market)
    elif args.command == "backfill":
        run_backfill()


if __name__ == "__main__":
    main()
