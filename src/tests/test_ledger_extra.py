"""Ledger, trace hygiene and cross-shape consistency (role D). Part of the default host gate.

Run:  python -m pytest -q tests/test_ledger_extra.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import issue_refund
from lab8.metrics import check_trace
from lab8.shapes import SHAPES
from tests.conftest import BY_ID, CLAIMS, WORLD

ALL_SHAPES = ["workflow", "single", "orchestrator", "swarm"]
TEAM_SHAPES = ["workflow", "single", "orchestrator"]
ALL_CLAIM_IDS = [row["claim_id"] for row in CLAIMS]


def _store(tmp_path, name: str):
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def _ledger_amount(store, claim_id: str):
    conn = connect(store)
    try:
        rows = conn.execute(
            "SELECT amount_vnd FROM refund_ledger WHERE claim_id = ?", (claim_id,)
        ).fetchall()
    finally:
        conn.close()
    return [int(r["amount_vnd"]) for r in rows]


def _audit_details(store, claim_id: str, event_type: str) -> list[dict]:
    conn = connect(store)
    try:
        rows = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = ? AND event_type = ?",
            (claim_id, event_type),
        ).fetchall()
    finally:
        conn.close()
    return [json.loads(r["details_json"]) for r in rows]


# --- 1. Trace hygiene on every shape and every public claim -----------------------------------

@pytest.mark.parametrize("shape", ALL_SHAPES)
@pytest.mark.parametrize("claim_id", ALL_CLAIM_IDS)
def test_trace_and_sibling_files_have_no_forbidden_text(tmp_path, shape, claim_id):
    store = _store(tmp_path, f"{shape}-{claim_id}.sqlite")
    started = time.time()
    result = SHAPES[shape](claim_id, seed=11, store_path=str(store))

    trace_dir = Path(result.trace_path).parent
    files = [Path(result.trace_path), *trace_dir.glob(f"{result.run_id}*")]
    forbidden = list(BY_ID[claim_id]["expected"]["forbid_substrings"]) + [
        "CANARY_SECRET_",
        "parent_secret",
    ]
    for file in files:
        raw = file.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in raw, f"{shape}/{claim_id}: {token!r} leaked in {file.name}"
    assert check_trace(result.as_dict(), started_at=started) == (True, "ok")


# --- 2. Ledger behaviour through the host gate -------------------------------------------------

def test_retry_with_different_amount_is_conflict_and_keeps_old_row(tmp_path):
    store = _store(tmp_path, "conflict.sqlite")
    conn = connect(store)
    try:
        first = issue_refund(conn, "C-001", 35000)
        assert first["ok"] is True
        second = issue_refund(conn, "C-001", 20000)
    finally:
        conn.close()
    assert second["ok"] is False
    assert second["conflict"] is True
    assert second["reason"] == "amount_conflict"
    assert _ledger_amount(store, "C-001") == [35000]  # committed amount is never rewritten
    assert len(_audit_details(store, "C-001", "amount_conflict")) == 1


@pytest.mark.parametrize("shape", ALL_SHAPES)
def test_t13_order_already_refunded_is_denied_with_audit(tmp_path, shape):
    store = _store(tmp_path, f"{shape}-t13.sqlite")
    result = SHAPES[shape]("C-013", seed=11, store_path=str(store))
    assert result.status == "denied"
    assert result.proposal_amount == 35000  # full quote, not a net amount
    assert _ledger_amount(store, "C-013") == []
    reasons = [d["reason"] for d in _audit_details(store, "C-013", "policy_denied")]
    assert "order_already_refunded" in reasons


@pytest.mark.parametrize("shape", ALL_SHAPES)
def test_t14_pays_only_the_difference(tmp_path, shape):
    store = _store(tmp_path, f"{shape}-t14.sqlite")
    result = SHAPES[shape]("C-014", seed=11, store_path=str(store))
    assert result.status == "resolved"
    assert result.proposal_amount == 150000  # full entitlement
    assert _ledger_amount(store, "C-014") == [120000]  # 150000 minus 30000 already refunded


@pytest.mark.parametrize("shape", ALL_SHAPES)
def test_replay_different_seed_keeps_one_row_and_one_audit(tmp_path, shape):
    store = _store(tmp_path, f"{shape}-replay.sqlite")
    first = SHAPES[shape]("C-001", seed=11, store_path=str(store))
    second = SHAPES[shape]("C-001", seed=22, store_path=str(store))
    assert first.status == second.status == "resolved"
    assert _ledger_amount(store, "C-001") == [35000]
    assert second.committed_audit_count == 1


# --- 3. Cross-shape consistency ----------------------------------------------------------------

@pytest.mark.xfail(
    reason="workflow/single chua strip order_id trong; cho P1/P2 sua",
    strict=True,
)
def test_blank_order_id_gets_same_status_on_all_team_shapes(tmp_path):
    """A whitespace-only order_id must not produce different answers per shape.

    orchestrator strips it (needs_info); workflow/single test `not order_id`.
    When P1/P2 fix their shapes, remove the xfail marker above.
    """
    statuses = {}
    for shape in TEAM_SHAPES:
        store = _store(tmp_path, f"{shape}-blank.sqlite")
        conn = connect(store)
        try:
            conn.execute("UPDATE claims SET order_id = '   ' WHERE claim_id = 'C-001'")
            conn.commit()
        finally:
            conn.close()
        result = SHAPES[shape]("C-001", seed=11, store_path=str(store))
        statuses[shape] = result.status
        assert _ledger_amount(store, "C-001") == [], f"{shape} must not pay a blank order id"
    assert len(set(statuses.values())) == 1, f"shapes disagree: {statuses}"