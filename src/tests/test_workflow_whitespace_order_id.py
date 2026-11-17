from __future__ import annotations

from lab8.db import connect
from lab8.shapes.workflow import run_claim
from tests.conftest import CLAIMS, WORLD
from lab8.db import init_store


def test_whitespace_only_order_id_needs_info_without_refund(tmp_path):
    claims = [dict(claim) for claim in CLAIMS]
    claim = next(row for row in claims if row["claim_id"] == "C-001")
    claim["order_id"] = "   "
    store = tmp_path / "workflow-whitespace-order-id.sqlite"
    init_store(store, WORLD, claims).close()

    result = run_claim("C-001", seed=11, store_path=str(store))

    assert result.status == "needs_info"
    assert result.proposal_amount == 0
    conn = connect(store)
    try:
        refunds = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?",
            ("C-001",),
        ).fetchone()["n"]
        assert refunds == 0
    finally:
        conn.close()
