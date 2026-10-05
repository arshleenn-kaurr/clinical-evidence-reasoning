#!/usr/bin/env python3
"""Phase 3, step 3: STRUCTURAL validation of accepted-paper canonical/raw files.
Read-only. Counts, IDs, coverage, schema shape and linkage only; it does not
summarize decisions or confidences. Writes validation/canonical_structure_report.json."""
import collections
import datetime
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter"
G = ROOT / "experiments/persistent_context/gemini_persistent_260/historical_package/agenticls_gemini_sequential"
A = ROOT / "experiments/persistent_context/gemini_aligned_control_40/historical_package/agenticls_aligned_persistent_control"
DEC = {"support", "do_not_support", "insufficient"}
C6 = ["H", "H_L1", "H_L2", "H_L4", "H_L4_ALIGNED", "L4_H"]


def load(p):
    rows, bad = [], 0
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return rows, bad


def schema_problems(r):
    p = []
    if r.get("decision") not in DEC:
        p.append("decision")
    c = r.get("confidence")
    if not isinstance(c, (int, float)) or not 0 <= c <= 100:
        p.append("confidence")
    if not isinstance(r.get("dominant_evidence_ids"), list):
        p.append("dominant_evidence_ids")
    if not isinstance(r.get("rationale"), str):
        p.append("rationale")
    return p


def check(ok, msg, problems):
    if not ok:
        problems.append(msg)
    return ok


def static_exp(name, canon, raw, cases, prompts, n_cases, expect_raw=None):
    problems = []
    cr, cbad = load(S / canon)
    cases_rows, _ = load(S / cases)
    prm, _ = load(S / prompts)
    ok = [r for r in cr if r.get("status") == "ok"]
    ids = collections.Counter(r["prompt_id"] for r in ok)
    expected_ids = {r["prompt_id"] for r in prm}
    case_ids = {c["case_id"] for c in cases_rows}
    cov = collections.defaultdict(set)
    for r in ok:
        cov[r["case_id"]].add(r["condition"])
    sch = collections.Counter(x for r in ok for x in schema_problems(r))
    conf_nonint = sum(1 for r in ok if isinstance(r.get("confidence"), float) and not float(r["confidence"]).is_integer())
    out = {
        "canonical_file": str((S / canon).relative_to(ROOT)), "canonical_sha256": hashlib.sha256((S / canon).read_bytes()).hexdigest(),
        "rows": len(cr), "malformed_rows": cbad, "status_counts": dict(collections.Counter(r.get("status") for r in cr)),
        "successful_rows": len(ok), "expected_successful": n_cases * 6,
        "unique_ids": len(ids), "duplicate_ids": sorted(k for k, v in ids.items() if v > 1),
        "missing_ids_vs_prompts": sorted(expected_ids - set(ids)), "unexpected_ids_vs_prompts": sorted(set(ids) - expected_ids),
        "cases_in_output": len(cov), "cases_in_cohort": len(case_ids), "cases_missing": sorted(case_ids - set(cov)),
        "cases_with_incomplete_conditions": sorted(c for c, s in cov.items() if s != set(C6)),
        "condition_counts": dict(collections.Counter(r["condition"] for r in ok)),
        "models": sorted({r.get("model") for r in ok}),
        "schema_problem_counts": dict(sch), "confidence_noninteger_values": conf_nonint,
    }
    check(len(ok) == n_cases * 6, f"successful rows {len(ok)} != {n_cases*6}", problems)
    check(not out["duplicate_ids"] and not out["missing_ids_vs_prompts"] and not out["unexpected_ids_vs_prompts"], "id coverage", problems)
    check(not out["cases_missing"] and not out["cases_with_incomplete_conditions"] and len(cov) == n_cases, "case/condition coverage", problems)
    check(cbad == 0 and not sch, "malformed/schema", problems)
    if raw and raw != canon:
        rr, rbad = load(S / raw)
        rok = [r for r in rr if r.get("status") == "ok"]
        rerr = [r for r in rr if r.get("status") != "ok"]
        err_types = collections.Counter(re.search(r"HTTP (\d+)", str(r.get("error"))).group(1) if re.search(r"HTTP (\d+)", str(r.get("error"))) else str(r.get("error"))[:40] for r in rerr)
        raw_ok_lines = [l for l in (S / raw).read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("status") == "ok"]
        canon_lines = [l for l in (S / canon).read_text(encoding="utf-8").splitlines() if l.strip()]
        err_ids = collections.Counter(r["prompt_id"] for r in rerr)
        retried_ok = all(ids.get(i) == 1 for i in err_ids)
        mapping = {
            "raw_file": str((S / raw).relative_to(ROOT)), "raw_rows": len(rr), "raw_malformed": rbad, "raw_ok": len(rok),
            "raw_error_rows": len(rerr), "raw_error_http_status": dict(err_types),
            "raw_identical_to_canonical_bytes": (S / raw).read_bytes() == (S / canon).read_bytes(),
            "canonical_equals_raw_ok_rows_in_order": canon_lines == raw_ok_lines,
            "canonical_line_set_equals_raw_ok_line_set": sorted(canon_lines) == sorted(raw_ok_lines),
            "every_failed_prompt_has_exactly_one_success": retried_ok,
        }
        out["raw_to_canonical"] = mapping
        if expect_raw:
            check(len(rr) == expect_raw[0] and len(rok) == expect_raw[1] and dict(err_types) == expect_raw[2], f"raw counts {len(rr)}/{len(rok)}/{dict(err_types)} != {expect_raw}", problems)
        check(mapping["canonical_line_set_equals_raw_ok_line_set"] or mapping["raw_identical_to_canonical_bytes"], "raw->canonical mapping", problems)
    out["problems"] = problems
    out["status"] = "STRUCTURE_VERIFIED" if not problems else "DISCREPANCY"
    return name, out


def order_from_log(p):
    d = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.search(r"\]\s+(\S+)\s+arm-first=(\S+)", line)
        if m:
            d.setdefault(m.group(1), set()).add(m.group(2))
    return d


def stratum(c):
    return f"{c['anchor']['evidence_quality']}|{c['reference_decision']}"


def gemini_260():
    problems = []
    res, bad = load(G / "results/gemini_260_results.jsonl")
    att, abad = load(G / "results/gemini_260_attempts.jsonl")
    cases, _ = load(G / "replication_cases_verified.jsonl")
    cmap = {c["case_id"]: c for c in cases}
    ok = [r for r in res if r.get("status") == "ok"]
    ids = collections.Counter(r["run_id"] for r in ok)
    need = [("sequential", c) for c in ["H", "H_L1", "H_L2", "H_L3", "H_L4"]] + [("fresh", "H_L4")]
    by = {(r["case_id"], r["arm"], r["condition"]) for r in ok}
    incomplete = sorted(c for c in cmap if not all((c, a, k) in by for a, k in need))
    expected_run_ids = {f"{c}::{a}::{k}" for c in cmap for a, k in need}
    sch = collections.Counter(x for r in ok for x in schema_problems(r))
    seq_struct = collections.Counter()
    for r in ok:
        if r["arm"] == "sequential":
            step = ["H", "H_L1", "H_L2", "H_L3", "H_L4"].index(r["condition"]) + 1
            if r.get("history_turns_before") != step - 1 or r.get("message_count") != 2 * (step - 1) + 1:
                seq_struct["history_or_message_count"] += 1
            if r.get("evidence_ids_available") != [f"E{i}" for i in range(step)]:
                seq_struct["cumulative_evidence_ids"] += 1
        else:
            if r.get("message_count") != 1 or r.get("evidence_ids_available") != [f"E{i}" for i in range(5)]:
                seq_struct["fresh_structure"] += 1
    http = collections.Counter(a.get("http_status") for a in att)
    att_ok_ids = collections.Counter(a["run_id"] for a in att if a.get("status") == "ok")
    order = order_from_log(G / "results/gemini_260_terminal.log")
    first = {k: next(iter(v)) for k, v in order.items() if len(v) == 1}
    by_stratum = collections.defaultdict(collections.Counter)
    for c, f in first.items():
        by_stratum[stratum(cmap[c])][f] += 1
    out = {
        "canonical_file": str((G / "results/gemini_260_results.jsonl").relative_to(ROOT)),
        "rows": len(res), "malformed_rows": bad, "status_counts": dict(collections.Counter(r.get("status") for r in res)),
        "successful_rows": len(ok), "expected_successful": 1560, "unique_run_ids": len(ids),
        "duplicate_run_ids": sorted(k for k, v in ids.items() if v > 1),
        "missing_run_ids": sorted(expected_run_ids - set(ids)), "unexpected_run_ids": sorted(set(ids) - expected_run_ids),
        "cases": len({r["case_id"] for r in ok}), "cases_incomplete": incomplete,
        "arm_condition_counts": {f"{a}:{k}": v for (a, k), v in collections.Counter((r["arm"], r["condition"]) for r in ok).items()},
        "schema_problem_counts": dict(sch), "sequential_structure_problems": dict(seq_struct),
        "attempts": {"rows": len(att), "malformed": abad, "http_status": {str(k): v for k, v in http.items()},
                     "ok_attempt_run_ids_equal_canonical": set(att_ok_ids) == set(ids) and all(v == 1 for v in att_ok_ids.values())},
        "execution_order": {"cases_in_log": len(order), "conflicting_labels": sum(len(v) > 1 for v in order.values()),
                            "overall": dict(collections.Counter(first.values())), "by_stratum": {k: dict(v) for k, v in sorted(by_stratum.items())}},
        "results_equal_FINAL_BACKUP": (G / "results/gemini_260_results.jsonl").read_bytes() == (G / "results/gemini_260_results_FINAL_BACKUP.jsonl").read_bytes(),
        "attempts_equal_FINAL_BACKUP": (G / "results/gemini_260_attempts.jsonl").read_bytes() == (G / "results/gemini_260_attempts_FINAL_BACKUP.jsonl").read_bytes(),
    }
    check(len(ok) == 1560 and len(ids) == 1560 and not out["missing_run_ids"] and not out["duplicate_run_ids"], "canonical counts/ids", problems)
    check(len(att) == 1567 and http == collections.Counter({200: 1560, 429: 5, 503: 2}), "attempt counts", problems)
    check(out["execution_order"]["overall"] == {"fresh": 130, "sequential": 130} or collections.Counter(first.values()) == collections.Counter({"fresh": 130, "sequential": 130}), "execution balance", problems)
    check(bad == 0 and abad == 0 and not sch and not seq_struct, "schema/structure", problems)
    out["problems"] = problems
    out["status"] = "STRUCTURE_VERIFIED" if not problems else "DISCREPANCY"
    return out


def aligned_40():
    problems = []
    res, bad = load(A / "results/aligned_control_results.jsonl")
    att, abad = load(A / "results/aligned_control_attempts.jsonl")
    cases, _ = load(A / "aligned_control_cases_40.jsonl")
    cmap = {c["case_id"]: c for c in cases}
    cohort_lines = set((G / "replication_cases_verified.jsonl").read_text(encoding="utf-8").splitlines())
    ok = [r for r in res if r.get("status") == "ok"]
    ids = collections.Counter(r["run_id"] for r in ok)
    need = [("aligned_sequential", f"H_L{i}_ALIGNED") for i in range(1, 5)] + [("fresh_aligned", "H_L4_ALIGNED")]
    expected = {f"{c}::{a}::{k}" for c in cmap for a, k in need}
    gres, _ = load(G / "results/gemini_260_results.jsonl")
    gidx = {r["run_id"]: r for r in gres}
    branch_ok = branch_n = 0
    for r in ok:
        if r["arm"] != "aligned_sequential":
            continue
        branch_n += 1
        s = gidx.get(r.get("source_h_run_id"))
        branch_ok += bool(s and s["arm"] == "sequential" and s["condition"] == "H" and s["case_id"] == r["case_id"]
                          and s["prompt_sha256"] == r["source_h_prompt_sha256"]
                          and hashlib.sha256(s["raw_text"].encode("utf-8")).hexdigest() == r["source_h_raw_text_sha256"]
                          and s["timestamp_utc"] == r["source_h_timestamp_utc"])
    order = order_from_log(A / "results/aligned_control_terminal.log")
    first = {k: next(iter(v)) for k, v in order.items() if len(v) == 1}
    by_stratum = collections.defaultdict(collections.Counter)
    for c, f in first.items():
        by_stratum[stratum(cmap[c])][f] += 1
    http = collections.Counter(a.get("http_status") for a in att)
    sch = collections.Counter(x for r in ok for x in schema_problems(r))
    out = {
        "canonical_file": str((A / "results/aligned_control_results.jsonl").relative_to(ROOT)),
        "cohort_sha256": hashlib.sha256((A / "aligned_control_cases_40.jsonl").read_bytes()).hexdigest(),
        "cohort_lines_subset_of_260": all(l in cohort_lines for l in (A / "aligned_control_cases_40.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()),
        "cases_per_stratum": dict(collections.Counter(stratum(c) for c in cases)),
        "rows": len(res), "malformed_rows": bad, "successful_rows": len(ok), "expected_successful": 200,
        "unique_run_ids": len(ids), "duplicate_run_ids": sorted(k for k, v in ids.items() if v > 1),
        "missing_run_ids": sorted(expected - set(ids)), "unexpected_run_ids": sorted(set(ids) - expected),
        "arm_condition_counts": {f"{a}:{k}": v for (a, k), v in collections.Counter((r["arm"], r["condition"]) for r in ok).items()},
        "schema_problem_counts": dict(sch),
        "attempts": {"rows": len(att), "malformed": abad, "http_status": {str(k): v for k, v in http.items()}},
        "branch_point_links_verified": f"{branch_ok}/{branch_n}",
        "execution_order": {"overall": dict(collections.Counter(first.values())), "by_stratum": {k: dict(v) for k, v in sorted(by_stratum.items())}},
    }
    check(out["cohort_sha256"] == "6d0fbdf6085d4373779bb5755bf3575ef812eecea98529656d3c58a30a3ff540", "cohort hash", problems)
    check(all(v == 10 for v in out["cases_per_stratum"].values()) and len(out["cases_per_stratum"]) == 4, "10 per stratum", problems)
    check(len(ok) == 200 and len(ids) == 200 and not out["missing_run_ids"], "canonical counts/ids", problems)
    check(len(att) == 200 and http == collections.Counter({200: 200}), "attempt counts", problems)
    check(branch_ok == branch_n == 160, "branch points", problems)
    check(all(v == {"fresh": 5, "sequential": 5} for v in out["execution_order"]["by_stratum"].values()), "5/5 order per stratum", problems)
    check(bad == 0 and abad == 0 and not sch, "schema", problems)
    out["problems"] = problems
    out["status"] = "STRUCTURE_VERIFIED" if not problems else "DISCREPANCY"
    return out


def main():
    g4h = dict([
        static_exp("gemini_primary_40", "results/final_main_gemini_3_6_flash.jsonl", None, "data/final_main_cases.jsonl", "data/final_main_prompts.jsonl", 40),
        static_exp("gemini_replication_260", "results/replication_gemini_3_6_flash_CLEAN.jsonl", "results/replication_gemini_3_6_flash_RAW.jsonl", "data/replication_cases.jsonl", "data/replication_prompts.jsonl", 260, (1564, 1560, {"503": 4})),
        static_exp("gemini_veto_15", "results/final_veto_gemini_3_6_flash.jsonl", None, "data/final_veto_cases.jsonl", "data/final_veto_prompts.jsonl", 15),
        static_exp("gpt_oss_primary_40", "results/final_main_gpt_oss_120b_CLEAN.jsonl", "results/final_main_gpt_oss_120b_RAW.jsonl", "data/final_main_cases.jsonl", "data/final_main_prompts.jsonl", 40),
        static_exp("gpt_oss_veto_15", "results/final_veto_gpt_oss_120b_CLEAN.jsonl", "results/final_veto_gpt_oss_120b_RAW.jsonl", "data/final_veto_cases.jsonl", "data/final_veto_prompts.jsonl", 15),
        static_exp("gemini_latent_v2_40", "results/latent_v2_main_gemini_3_6_flash_CLEAN.jsonl", "results/latent_v2_main_gemini_3_6_flash_RAW.jsonl", "data/final_main_cases.jsonl", "data/latent_v2_main_prompts.jsonl", 40),
    ])
    report = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "note": "Structural only; no outcome summaries computed.",
              "genai4health": g4h, "agenticls": {"gemini_persistent_260": gemini_260(), "gemini_aligned_control_40": aligned_40()}}
    (ROOT / "validation/canonical_structure_report.json").write_text(json.dumps(report, indent=2) + "\n")
    for paper in ("genai4health", "agenticls"):
        for k, v in report[paper].items():
            print(f"{paper}/{k}: {v['status']} {v['problems']}")


if __name__ == "__main__":
    main()
