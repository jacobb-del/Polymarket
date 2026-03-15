from datetime import datetime, timezone

from src.models.score import CandidateRow, ScoreBreakdown
from src.services.storage import Storage


def test_storage_init_and_insert(tmp_path) -> None:
    db = tmp_path / "test.db"
    storage = Storage(str(db))
    storage.init()

    candidate = CandidateRow(
        market_id="m1",
        event_id="e1",
        title="Test",
        slug="test",
        best_bid=0.08,
        best_ask=0.1,
        spread=0.02,
        top_depth=70,
        fees_enabled=False,
        catalyst_hours=12,
        score=ScoreBreakdown("m1", 0.7, 0.6, 0.5, 0.4, 0.1, 0.58, []),
    )
    storage.persist_candidates([candidate])

    import sqlite3

    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT market_id, total_score FROM scan_candidates").fetchall()

    assert rows == [("m1", 0.58)]
