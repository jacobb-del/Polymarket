from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover
    def load_dotenv() -> None:
        return None


@dataclass(slots=True)
class Settings:
    gamma_base_url: str = "https://gamma-api.polymarket.com"
    clob_base_url: str = "https://clob.polymarket.com"
    db_path: str = "data/scanner.db"
    scan_interval_seconds: int = 60
    min_price: float = 0.03
    max_price: float = 0.18
    catalyst_min_hours: int = 6
    catalyst_max_days: int = 10
    min_top_book_depth: float = 50.0
    max_spread: float = 0.08
    top_n: int = 20
    alert_score_threshold: float = 0.55
    fee_rate_bps: float = 0.0

    weight_catalyst: float = 0.30
    weight_liquidity: float = 0.25
    weight_asymmetry: float = 0.25
    weight_movement: float = 0.20

    request_timeout_seconds: int = 15


def load_settings() -> Settings:
    load_dotenv()
    d = Settings()
    return Settings(
        gamma_base_url=os.getenv("GAMMA_BASE_URL", d.gamma_base_url),
        clob_base_url=os.getenv("CLOB_BASE_URL", d.clob_base_url),
        db_path=os.getenv("DB_PATH", d.db_path),
        scan_interval_seconds=int(os.getenv("SCAN_INTERVAL_SECONDS", str(d.scan_interval_seconds))),
        min_price=float(os.getenv("MIN_PRICE", str(d.min_price))),
        max_price=float(os.getenv("MAX_PRICE", str(d.max_price))),
        catalyst_min_hours=int(os.getenv("CATALYST_MIN_HOURS", str(d.catalyst_min_hours))),
        catalyst_max_days=int(os.getenv("CATALYST_MAX_DAYS", str(d.catalyst_max_days))),
        min_top_book_depth=float(os.getenv("MIN_TOP_BOOK_DEPTH", str(d.min_top_book_depth))),
        max_spread=float(os.getenv("MAX_SPREAD", str(d.max_spread))),
        top_n=int(os.getenv("TOP_N", str(d.top_n))),
        alert_score_threshold=float(os.getenv("ALERT_SCORE_THRESHOLD", str(d.alert_score_threshold))),
        fee_rate_bps=float(os.getenv("FEE_RATE_BPS", str(d.fee_rate_bps))),
        weight_catalyst=float(os.getenv("WEIGHT_CATALYST", str(d.weight_catalyst))),
        weight_liquidity=float(os.getenv("WEIGHT_LIQUIDITY", str(d.weight_liquidity))),
        weight_asymmetry=float(os.getenv("WEIGHT_ASYMMETRY", str(d.weight_asymmetry))),
        weight_movement=float(os.getenv("WEIGHT_MOVEMENT", str(d.weight_movement))),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", str(d.request_timeout_seconds))),
    )


def ensure_data_dir(settings: Settings) -> None:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
