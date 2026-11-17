"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "orchestrator"
# Investigators are read-only. No issue_refund / append_audit: make_handoff rejects them.
# compute_compensation reads the current policy itself, so lookup_policy would be a wasted tool call.
INVESTIGATOR_TOOLS = ["lookup_order", "compute_compensation"]


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at, budget=budget, trace=trace)
    except InjectedCrash:
        raise  # the crash is the point of T12: never swallow it
    except Exception as exc:
        # run_claim must not throw (docs/contracts.md): report a failed trial with a clean trace.
        trace.add("error", {"reason": type(exc).__name__})
        return _end(conn, claim_id, seed, "failed", 0, budget, trace, type(exc).__name__)
    finally:
        conn.close()


def _end(conn, claim_id, seed, status, amount, budget, trace, reason=None) -> RunResult:
    return finish(
        conn,
        shape=SHAPE,
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=amount,
        budget=budget,
        trace=trace,
        error_reason=reason,
    )


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
    budget: Budget,
    trace: Trace,
) -> RunResult:
    # 1. Orchestrator reads the claim through the allowlisted view. The ticket is user
    #    data: it is never parsed for numbers or order ids, and never written to the trace.
    claim = get_claim_view(conn, claim_id)
    budget.add_tool(tool_cost())
    if not claim.get("found"):
        trace.add("error", {"reason": "unknown_claim"})
        return _end(conn, claim_id, seed, "failed", 0, budget, trace, "unknown_claim")

    # Blank means missing (needs_info). A non-blank id is looked up exactly as stored: the host
    # matches order ids exactly too, so a padded or look-alike id is "not found" (escalated).
    order_id = (claim.get("order_id") or "").strip()
    trace.add("claim", {"claim_id": claim_id, "has_order_id": bool(order_id)})
    if not order_id:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return _end(conn, claim_id, seed, "needs_info", 0, budget, trace, "missing_order_id")

    # 2. Plan, then delegate. The handoff carries only allowlisted fields; the parent
    #    context (claim row, ticket text, secrets) is not forwarded or traced.
    complete(budget, seed=seed, purpose="plan", prompt=f"delegate:{claim_id}")
    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_applicable_policy",
        facts={},
        allowed_tools=INVESTIGATOR_TOOLS,
    )
    trace.add("handoff", safe_dump(handoff))

    investigated = run_readonly_investigators(conn, budget, handoff, principal_id=claim["principal_id"])
    order_view = investigated["tools"].get("lookup_order", {})
    # When the order is not visible, log only the verdict: the looked-up id is user-controlled text.
    seen = order_view if order_view.get("visible") else {"visible": False, "reason": order_view.get("reason")}
    trace.add("investigator", {"lookup_order": seen})

    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        trace.add("decision", {"status": "escalated", "reason": order_view.get("reason")})
        return _end(conn, claim_id, seed, "escalated", 0, budget, trace, order_view.get("reason"))

    # 3. Money comes from the investigator's compute_compensation over the DB order row.
    quote_payload = investigated["tools"].get("compute_compensation") or {}
    proposal = int(quote_payload.get("amount_vnd", 0))
    trace.add("quote", safe_dump(quote_payload))
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return _end(conn, claim_id, seed, "denied", 0, budget, trace, quote_payload.get("reason"))

    # 4. Only the orchestrator writes, through the host gate, with the FULL quote.
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add("host", {"ok": outcome["ok"], "reason": outcome["reason"], "conflict": outcome["conflict"]})
    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return _end(conn, claim_id, seed, status, proposal, budget, trace, outcome["reason"])
    return _end(conn, claim_id, seed, "resolved", proposal, budget, trace, None)
