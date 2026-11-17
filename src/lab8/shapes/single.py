"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import ToolRejected, run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "single"
MAX_STEPS = 8


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, amount: int, reason: str | None) -> RunResult:
        return finish(
            conn, shape=SHAPE, claim_id=claim_id, seed=seed, status=status,
            proposal_amount=amount, budget=budget, trace=trace, error_reason=reason,
        )

    # 1. Đọc claim qua tool allowlist (không đụng parent_secret / raw_headers).
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        trace.add("error", {"reason": "unknown_claim"})
        return done("failed", 0, "unknown_claim")

    # 2. Thiếu order_id -> needs_info. Không lấy mã đơn từ chữ trong ticket.
    if not claim["order_id"]:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        trace.add("decision", {"status": "needs_info"})
        return done("needs_info", 0, "missing_order_id")

    # Ticket là dữ liệu không tin cậy: KHÔNG đưa vào observation, KHÔNG ghi trace.
    observation = {
        "claim": {k: claim[k] for k in ("claim_id", "principal_id", "order_id")},
    }
    state: dict = {"quote": None}

    def decide(obs: dict) -> dict:
        complete(budget, seed=seed, purpose="react", prompt=f"step:{obs.get('last_tool') or 'start'}")
        last = obs.get("last_tool")
        if last is None:
            c = obs["claim"]
            return {"tool": "lookup_order", "args": {"order_id": c["order_id"], "principal_id": c["principal_id"]}}
        result = obs["last_result"]
        if last == "lookup_order":
            trace.add("observation", {"tool": last, "result": result})
            if not result.get("visible"):
                return {"final": {"status": "escalated", "reason": result.get("reason")}}
            return {"tool": "compute_compensation", "args": {"order": result["order"]}}
        if last == "compute_compensation":
            trace.add("quote", result)
            state["quote"] = result
            if int(result["amount_vnd"]) <= 0:
                return {"final": {"status": "quote", "amount": 0, "reason": result.get("reason")}}
            c = obs["claim"]
            return {"tool": "lookup_refund_history", "args": {"order_id": c["order_id"], "principal_id": c["principal_id"]}}
        if last == "lookup_refund_history":
            trace.add("observation", {"tool": last, "result": result})
            q = state["quote"]
            return {"final": {"status": "quote", "amount": int(q["amount_vnd"]), "reason": q.get("reason")}}
        return {"final": {"status": "failed", "reason": "unexpected_state"}}

    try:
        loop = run_react(conn, budget, observation=observation, decide=decide, max_steps=MAX_STEPS, worker=False)
    except ToolRejected as exc:
        trace.add("error", {"reason": "tool_rejected", "detail": str(exc)})
        return done("failed", 0, "tool_rejected")

    final = loop["final"]
    trace.add("decision", {"stopped": loop["stopped"], "final": final})
    if loop["stopped"] != "final" or final["status"] == "failed":
        return done("failed", 0, final.get("reason") or final.get("error_reason") or "step_cap")
    if final["status"] == "escalated":
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return done("escalated", 0, final.get("reason"))

    # 3. Sau vòng lặp: code của shape (không phải model) quyết định ghi.
    amount = int(final["amount"])
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={amount}")
    if amount <= 0:
        return done("denied", 0, final.get("reason"))

    # 4. Truyền QUOTE ĐẦY ĐỦ + crash_at; không bắt InjectedCrash (chỉ flush trace rồi ném lại).
    try:
        outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        trace.add("host_denied", {"reason": outcome["reason"]})
        return done("failed" if outcome["conflict"] else "denied", amount, outcome["reason"])
    return done("resolved", amount, None)
