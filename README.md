# Polymarket Pre-Resolution Repricing Scanner (MVP)

Beginner-friendly Python MVP for finding **low-priced Polymarket outcomes** that may reprice before final resolution because of a near-term catalyst.

> v1 scope: scanner + alerts + SQLite + paper trading simulation.
> No live order placement, no private keys, no real trading.

## What this project does

- Discovers active markets from Polymarket Gamma APIs.
- Keeps only tradable, order-book-enabled markets.
- Pulls order-book top-of-book data from CLOB endpoints.
- Scores repricing potential with transparent weighted factors.
- Outputs ranked candidates in terminal + JSON + SQLite.
- Supports manual catalyst tagging (`catalysts.yaml`).
- Simulates paper trades only (entry/exit assumptions + PnL).

## Project structure

```text
src/
  config.py
  clients/
    polymarket_gamma.py
    polymarket_clob.py
    websocket_client.py
  models/
    market.py
    score.py
    paper_trade.py
  services/
    market_loader.py
    market_filter.py
    scorer.py
    alerting.py
    paper_engine.py
    storage.py
  main.py
tests/
.env.example
catalysts.yaml
```

## Quick start (step by step)

1. **Install Python 3.11+**
2. **Clone repo and enter folder**
3. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
5. **Create local env file**
   ```bash
   cp .env.example .env
   ```
6. **Run scanner**
   ```bash
   python -m src.main scan
   ```
7. **Review output**
   - Terminal table of top candidates
   - `data/shortlist.json`
   - `data/scanner.db`

## CLI commands

```bash
python -m src.main scan
python -m src.main shortlist
python -m src.main stream
python -m src.main paper-trade --market <market_id>
python -m src.main backfill
```

## Scoring model (v1)

```text
score =
  catalyst_score * 0.30 +
  liquidity_score * 0.25 +
  asymmetry_score * 0.25 +
  movement_score * 0.20 -
  friction_penalty
```

Editable via `.env` weights.

### Factors
- **Catalyst score**: timing + confidence of catalyst.
- **Liquidity score**: spread and top-of-book depth.
- **Asymmetry score**: cheap entry with room to reprice.
- **Movement score**: simple keyword heuristic for event-driven narratives.
- **Friction penalty**: fee-enabled markets, wide spreads, thin depth, unclear rules.

## Catalyst modes

1. **Automatic mode**: falls back to market `endDate`/resolution-like timestamps.
2. **Manual mode**: `catalysts.yaml` by slug/title keyword with datetime + confidence.

## Paper trading (simulation only)

- Entry at ask (or basic limit assumption)
- Exit at bid
- Includes spread cost
- Optional fee impact (if enabled and configured)
- Supports exit labels: take-profit, time-stop, liquidity-stop
- Logs simulated trades to SQLite

## Sample output

See: `data/sample_shortlist.json`

## Testing

```bash
pytest
```

## Manual API verification still needed

Public Polymarket endpoints can evolve. This MVP isolates assumptions but you should verify these in your environment:

1. **Gamma market schema**
   - Confirm exact field names for:
     `enableOrderBook`, `feesEnabled`, `eventId`, token list, end/resolution timestamps.
2. **CLOB orderbook schema**
   - Confirm `GET /book?token_id=...` response shape (`bids/asks`, `price/size`).
3. **WebSocket URL and channels**
   - Confirm the canonical production websocket endpoint and subscription message format.
4. **Fee model details**
   - Confirm how fees are charged (maker/taker, side, notional basis).
5. **Rate limits**
   - Validate polling intervals for stable production usage.

## Safety and scope guardrails

- No private key handling.
- No order-signing code.
- No live trading execution.
- Use for alerts + research + paper simulations only.
