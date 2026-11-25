#!/usr/bin/env python3
"""Operational-only validator for the 10-case Gemini smoke test.

Deliberately reports no decisions, confidence summaries, effect sizes, or
scientific outcomes.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

SEQ_CONDS = ["H", "H_L1", "H_L2", "H_L3", "H_L4"]


def load(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.open(encoding="utf-8") if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--expected-cases", type=int, default=10)
    args = ap.parse_args()

    rows = load(args.results)
    ok = [r for r in rows if r.get("status") == "ok"]
    errors = [r for r in rows if r.get("status") != "ok"]
    by = {(r["case_id"], r["arm"], r["condition"]): r for r in ok}
    case_ids = sorted({r["case_id"] for r in rows})
    problems = []

    if len(case_ids) != args.expected_cases:
        problems.append(f"expected {args.expected_cases} cases, found {len(case_ids)}")

    for cid in case_ids:
        for step, cond in enumerate(SEQ_CONDS, 1):
            key = (cid, "sequential", cond)
            if key not in by:
                problems.append(f"missing successful row: {cid} sequential {cond}")
                continue
            r = by[key]
            expected_ids = [f"E{i}" for i in range(step)]
            if r.get("step") != step:
                problems.append(f"bad step: {cid} sequential {cond}")
            if r.get("evidence_ids_available") != expected_ids:
                problems.append(f"bad cumulative evidence IDs: {cid} sequential {cond}")
            if r.get("history_turns_before") != step - 1:
                problems.append(f"bad history_turns_before: {cid} {cond}")
            if r.get("message_count") != 2 * (step - 1) + 1:
                problems.append(f"bad sequential message_count: {cid} {cond}")
            expected_new = "E0" if step == 1 else f"E{step-1}"
            if r.get("new_evidence_id") != expected_new:
                problems.append(f"bad new evidence ID: {cid} {cond}")
            if r.get("model") != "gemini-3.6-flash":
                problems.append(f"unexpected model: {cid} {cond}")
            if r.get("temperature_sent") is not None:
                problems.append(f"sampling temperature unexpectedly sent: {cid} {cond}")
            if r.get("response_schema_mode") != "responseJsonSchema":
                problems.append(f"unexpected schema mode: {cid} {cond}")

        fkey = (cid, "fresh", "H_L4")
        if fkey not in by:
            problems.append(f"missing successful row: {cid} fresh H_L4")
        else:
            r = by[fkey]
            if r.get("step") != 5:
                problems.append(f"bad fresh step: {cid}")
            if r.get("evidence_ids_available") != ["E0", "E1", "E2", "E3", "E4"]:
                problems.append(f"bad fresh terminal evidence IDs: {cid}")
            if r.get("message_count") != 1:
                problems.append(f"fresh message_count != 1: {cid}")
            if r.get("model") != "gemini-3.6-flash":
                problems.append(f"unexpected fresh model: {cid}")

    duplicate_ok = [k for k, n in Counter(r["run_id"] for r in ok).items() if n > 1]
    if duplicate_ok:
        problems.append(f"duplicate successful run_ids: {duplicate_ok[:5]}")
    if errors:
        problems.append(f"canonical result file contains {len(errors)} error row(s)")

    print("GEMINI SMOKE TEST OPERATIONAL VALIDATION")
    print(f"cases_seen: {len(case_ids)}")
    print(f"successful_rows: {len(ok)}")
    print(f"expected_successful_rows: {args.expected_cases * 6}")
    print(f"operational_status: {'PASS' if not problems else 'FAIL'}")
    if problems:
        print("problems:")
        for p in problems:
            print(" -", p)
        raise SystemExit(1)
    print("No scientific result summaries were computed by this validator.")


if __name__ == "__main__":
    main()
