"""Orchestrator: handoff boundary, trace hygiene, crash and retry (P3). Part of the default host gate."""

from __future__ import annotations

import json
import time

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.handoff import ALLOWED_FIELDS, READONLY_TOOLS
from lab8.metrics import check_trace
from lab8.schemas import make_run_id
from lab8.shapes.orchestrator import run_claim
from tests.conftest import BY_ID, CLAIMS

ALL_CLAIM_IDS = [row["claim_id"] for row in CLAIMS]


def _events(result, kind: str) -> list[dict]:
    with open(result.trace_path, encoding="utf-8") as handle:
        events = json.load(handle)["events"]
    return [event["payload"] for event in events if event["kind"] == kind]


def _ledger_rows(store, claim_id: str) -> int:
    conn = connect(store)
    try:
        return conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (claim_id,)).fetchone()["n"]
    finally:
        conn.close()


def test_handoff_in_trace_is_allowlisted_and_read_only(public_db):
    result = run_claim("C-010", seed=11, store_path=str(public_db))
    handoffs = _events(result, "handoff")
    assert len(handoffs) == 1
    handoff = handoffs[0]
    assert set(handoff) <= ALLOWED_FIELDS
    assert set(handoff["allowed_tools"]) <= READONLY_TOOLS
    assert "issue_refund" not in handoff["allowed_tools"]
    assert "parent_secret" not in handoff
    # Nothing from the claim or ticket is forwarded: facts stay empty, so no value can leak through them.
    assert handoff["facts"] == {}
    assert BY_ID["C-010"]["ticket"] not in json.dumps(handoff, ensure_ascii=False)


@pytest.mark.parametrize("claim_id", ALL_CLAIM_IDS)
def test_trace_never_carries_secret_pii_or_ticket(public_db, claim_id):
    started = time.time()
    result = run_claim(claim_id, seed=11, store_path=str(public_db))
    raw = open(result.trace_path, encoding="utf-8").read()
    # Every token the public matrix forbids (secrets, phone, address, item, internal note).
    for token in BY_ID[claim_id]["expected"]["forbid_substrings"]:
        assert token not in raw, token
    # The ticket is user text. It must not appear under any key, not just a key named "ticket".
    ticket = BY_ID[claim_id]["ticket"]
    assert ticket not in raw
    assert json.dumps(ticket, ensure_ascii=False).strip('"') not in raw
    assert "CANARY_SECRET_" not in raw
    assert "parent_secret" not in raw
    assert '"ticket"' not in raw
    assert check_trace(result.as_dict(), started_at=started) == (True, "ok")


def test_ticket_delay_is_ignored(public_db):
    # C-002: ticket says 5 days, order row says 2. The orchestrator must trust the order row,
    # including on seed 55 where the swarm reference is fooled.
    result = run_claim("C-002", seed=55, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []


def test_unknown_claim_fails_without_raising(public_db):
    started = time.time()
    result = run_claim("C-999", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.proposal_amount == 0
    assert result.error_reason == "unknown_claim"
    assert check_trace(result.as_dict(), started_at=started) == (True, "ok")


def test_missing_order_id_is_needs_info_and_writes_nothing(public_db):
    result = run_claim("C-004", seed=11, store_path=str(public_db))
    assert result.status == "needs_info"
    assert _ledger_rows(public_db, "C-004") == 0
    assert _events(result, "handoff") == []  # nothing delegated without an order


def test_replay_keeps_one_refund_and_one_committed_audit(public_db):
    first = run_claim("C-001", seed=11, store_path=str(public_db))
    second = run_claim("C-001", seed=22, store_path=str(public_db))
    assert first.status == second.status == "resolved"
    assert _ledger_rows(public_db, "C-001") == 1
    assert second.committed_audit_count == 1


@pytest.mark.parametrize("crash_at", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_crash_is_not_swallowed_and_resume_pays_once(public_db, tmp_path, monkeypatch, crash_at):
    monkeypatch.chdir(tmp_path)  # Trace writes to ./traces, keep it away from stale files
    with pytest.raises(InjectedCrash):
        run_claim("C-012", seed=11, store_path=str(public_db), crash_at=crash_at)
    crashed_trace = tmp_path / "traces" / f"{make_run_id('orchestrator', 'C-012', 11)}.json"
    body = json.loads(crashed_trace.read_text(encoding="utf-8"))
    assert any(event["kind"] == "crash" for event in body["events"])

    resumed = run_claim("C-012", seed=11, store_path=str(public_db))
    assert resumed.status == "resolved"
    assert _ledger_rows(public_db, "C-012") == 1
    assert resumed.committed_audit_count == 1


def _store_with_order_id(tmp_path, order_id):
    """Public world, but C-001 points at `order_id` instead of its real order."""
    from lab8.db import init_store
    from tests.conftest import WORLD

    claims = [dict(row) for row in CLAIMS]
    for row in claims:
        if row["claim_id"] == "C-001":
            row["order_id"] = order_id
    path = tmp_path / "custom.sqlite"
    init_store(path, WORLD, claims).close()
    return path


@pytest.mark.parametrize(
    ("order_id", "status"),
    [
        ("   ", "needs_info"),  # blank means missing
        ("\t\n", "needs_info"),
        ("O-107 ", "escalated"),  # padded id: host matches exactly, so "not found"
        (" O-107", "escalated"),
        ("\u041e-107", "escalated"),  # Cyrillic O look-alike
        ("o-107", "escalated"),
    ],
)
def test_blank_vs_padded_order_id_decision(tmp_path, order_id, status):
    store = _store_with_order_id(tmp_path, order_id)
    result = run_claim("C-001", seed=11, store_path=str(store))
    assert result.status == status
    assert result.proposal_amount == 0
    assert _ledger_rows(store, "C-001") == 0


def test_unexpected_error_becomes_failed_not_exception(public_db, monkeypatch):
    started = time.time()

    def boom(**_kwargs):
        raise RuntimeError("investigator crashed")

    monkeypatch.setattr("lab8.shapes.orchestrator.make_handoff", boom)
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "RuntimeError"
    assert _ledger_rows(public_db, "C-001") == 0
    assert check_trace(result.as_dict(), started_at=started) == (True, "ok")


def test_not_found_order_id_is_not_written_to_trace(tmp_path):
    marker = "O-NOT-A-REAL-ORDER-777"
    store = _store_with_order_id(tmp_path, marker)
    result = run_claim("C-001", seed=11, store_path=str(store))
    assert result.status == "escalated"
    assert marker not in open(result.trace_path, encoding="utf-8").read()
