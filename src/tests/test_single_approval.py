"""Shape B (single): các nhánh approval. Host phải chặn, shape phải trả đúng RunResult."""

from __future__ import annotations

from pathlib import Path

import pytest

from lab8.db import connect
from lab8.shapes import SHAPES

SEEDS = [11, 22, 33, 44, 55]
ORDER = "O-808"  # đơn của P-100, quote ship = 35000 (xem C-008 / T08)


def _setup(db: Path, claim_id: str, approval_id: str | None, approval: dict | None = None) -> None:
    conn = connect(db)
    if approval is not None:
        conn.execute(
            "INSERT INTO approvals (approval_id, claim_id, approved_vnd, status, expires_at) VALUES (?, ?, ?, ?, ?)",
            (
                approval["id"],
                approval.get("claim_id", claim_id),
                approval.get("amount", 35000),
                approval.get("status", "valid"),
                approval.get("expires", "2027-12-31"),
            ),
        )
    conn.execute(
        """
        INSERT INTO claims (claim_id, principal_id, order_id, ticket, parent_secret, raw_headers_json, approval_id)
        VALUES (?, 'P-100', ?, 'Đơn giao trễ 4 ngày, hoàn phí ship.', 'CANARY_SECRET_PARENT_X', '{}', ?)
        """,
        (claim_id, ORDER, approval_id),
    )
    conn.commit()
    conn.close()


def _state(db: Path, claim_id: str):
    conn = connect(db)
    try:
        ledger = conn.execute("SELECT amount_vnd FROM refund_ledger WHERE claim_id = ?", (claim_id,)).fetchall()
        denied = [
            r["details_json"]
            for r in conn.execute(
                "SELECT details_json FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
                (claim_id,),
            )
        ]
        committed = conn.execute(
            "SELECT COUNT(*) AS n FROM audit_events WHERE claim_id = ? AND event_type = 'refund_committed'",
            (claim_id,),
        ).fetchone()["n"]
    finally:
        conn.close()
    return ledger, denied, committed


CASES = [
    ("no_approval_id", None, None, "missing_approval"),
    ("approval_row_missing", "A-GHOST", None, "missing_approval"),
    ("expired", "A-X", {"id": "A-X", "expires": "2020-01-01"}, "approval_expired"),
    ("revoked", "A-X", {"id": "A-X", "status": "revoked"}, "approval_revoked"),
    ("other_claim", "A-X", {"id": "A-X", "claim_id": "C-OTHER"}, "approval_claim_mismatch"),
    ("zero_amount", "A-X", {"id": "A-X", "amount": 0}, "non_positive_amount"),
]


@pytest.mark.parametrize("name,approval_id,approval,reason", CASES, ids=[c[0] for c in CASES])
def test_single_blocked_approval_writes_nothing(public_db, name, approval_id, approval, reason):
    # Một seed là đủ: nhánh approval do host quyết, decide() không phụ thuộc seed.
    # Tính không phụ thuộc seed được kiểm riêng ở test_single_blocked_result_is_seed_independent.
    claim_id = f"C-SGL-{name}"
    _setup(public_db, claim_id, approval_id, approval)
    result = SHAPES["single"](claim_id, seed=11, store_path=str(public_db))
    ledger, denied, committed = _state(public_db, claim_id)

    assert result.status == "denied"
    assert result.proposal_amount == 35000  # quote đầy đủ, không phải 0
    assert result.refund_effects == []
    assert ledger == [] and committed == 0
    assert any(reason in row for row in denied), denied  # host ghi audit policy_denied
    assert "CANARY_SECRET" not in Path(result.trace_path).read_text(encoding="utf-8")


def test_single_blocked_result_is_seed_independent(tmp_path):
    """Cùng một approval hỏng, 5 seed phải ra cùng status, cùng quote, cùng lý do audit."""
    from lab8.db import init_store
    from tests.conftest import CLAIMS, WORLD

    outcomes = set()
    for seed in SEEDS:
        db = tmp_path / f"seed-{seed}.sqlite"
        init_store(db, WORLD, CLAIMS).close()
        _setup(db, "C-SGL-seed", "A-X", {"id": "A-X", "claim_id": "C-OTHER"})
        result = SHAPES["single"]("C-SGL-seed", seed=seed, store_path=str(db))
        ledger, denied, _ = _state(db, "C-SGL-seed")
        assert ledger == []
        outcomes.add((result.status, result.proposal_amount, tuple(denied)))
    assert len(outcomes) == 1, outcomes


@pytest.mark.parametrize("order_id", ["", "   ", "\t"], ids=["empty", "spaces", "tab"])
def test_single_blank_order_id_is_needs_info(public_db, order_id):
    """order_id rỗng hoặc toàn khoảng trắng: needs_info, không gọi host, không ghi gì."""
    conn = connect(public_db)
    conn.execute("UPDATE claims SET order_id = ? WHERE claim_id = 'C-001'", (order_id,))
    conn.commit()
    conn.close()
    result = SHAPES["single"]("C-001", seed=11, store_path=str(public_db))
    ledger, denied, committed = _state(public_db, "C-001")
    assert result.status == "needs_info"
    assert result.proposal_amount == 0
    assert ledger == [] and denied == [] and committed == 0


def test_single_lower_approval_caps_amount_but_keeps_full_quote(public_db):
    _setup(public_db, "C-SGL-low", "A-LOW", {"id": "A-LOW", "amount": 20000})
    result = SHAPES["single"]("C-SGL-low", seed=11, store_path=str(public_db))
    ledger, denied, committed = _state(public_db, "C-SGL-low")
    assert result.status == "resolved"
    assert result.proposal_amount == 35000
    assert [r["amount_vnd"] for r in ledger] == [20000]
    assert committed == 1 and denied == []


def test_single_replay_after_denied_stays_denied(public_db):
    _setup(public_db, "C-SGL-replay", "A-X", {"id": "A-X", "status": "revoked"})
    first = SHAPES["single"]("C-SGL-replay", seed=11, store_path=str(public_db))
    second = SHAPES["single"]("C-SGL-replay", seed=11, store_path=str(public_db))
    ledger, _, _ = _state(public_db, "C-SGL-replay")
    assert first.status == second.status == "denied"
    assert ledger == []
