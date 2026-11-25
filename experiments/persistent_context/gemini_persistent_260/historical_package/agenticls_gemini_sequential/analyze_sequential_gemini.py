#!/usr/bin/env python3
"""Frozen analysis for the optimized Gemini persistent-context experiment.

By default this REFUSES to analyze an incomplete 260-case main run.
Uses only Python standard library.
"""
import argparse
import json
import math
import random
from collections import Counter
from pathlib import Path

CONDS = ["H", "H_L1", "H_L2", "H_L3", "H_L4"]


def load(path):
    return [json.loads(x) for x in open(path, encoding="utf-8") if x.strip()]


def binom_pmf(n, k, p):
    if p == 0.0:
        return 1.0 if k == 0 else 0.0
    if p == 1.0:
        return 1.0 if k == n else 0.0
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def binom_cdf(n, k, p):
    return sum(binom_pmf(n, j, p) for j in range(0, k + 1))


def binom_sf_ge(n, k, p):
    return sum(binom_pmf(n, j, p) for j in range(k, n + 1))


def clopper_pearson(k, n, alpha=0.05):
    if n == 0:
        return [None, None]
    if k == 0:
        lo = 0.0
    else:
        a, b = 0.0, 1.0
        target = alpha / 2
        for _ in range(70):
            m = (a + b) / 2
            # P(X >= k) increases with p.
            if binom_sf_ge(n, k, m) < target:
                a = m
            else:
                b = m
        lo = (a + b) / 2
    if k == n:
        hi = 1.0
    else:
        a, b = 0.0, 1.0
        target = alpha / 2
        for _ in range(70):
            m = (a + b) / 2
            # P(X <= k) decreases with p.
            if binom_cdf(n, k, m) > target:
                a = m
            else:
                b = m
        hi = (a + b) / 2
    return [lo, hi]


def quantile(xs, q):
    s = sorted(xs)
    if not s:
        return None
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    return s[lo] * (hi - pos) + s[hi] * (pos - lo)


def median(xs):
    return quantile(xs, 0.5)


def bootstrap_mean_ci(xs, B=100000, seed=20260922):
    if not xs:
        return [None, None]
    rng = random.Random(seed)
    n = len(xs)
    means = []
    for _ in range(B):
        means.append(sum(xs[rng.randrange(n)] for _ in range(n)) / n)
    return [quantile(means, 0.025), quantile(means, 0.975)]


def mcnemar_exact(a_correct, b_correct):
    b = sum(x and not y for x, y in zip(a_correct, b_correct))
    c = sum((not x) and y for x, y in zip(a_correct, b_correct))
    n = b + c
    if n == 0:
        return {"b": b, "c": c, "p": 1.0}
    k = min(b, c)
    tail = sum(math.comb(n, j) for j in range(k + 1)) / (2 ** n)
    return {"b": b, "c": c, "p": min(1.0, 2 * tail)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--out")
    ap.add_argument("--expected-cases", type=int, default=260)
    ap.add_argument("--bootstrap", type=int, default=100000)
    ap.add_argument("--allow-incomplete", action="store_true")
    args = ap.parse_args()

    rows = load(args.results)
    ok = [r for r in rows if r.get("status") == "ok"]
    errors = [r for r in rows if r.get("status") != "ok"]
    dupes = [k for k, v in Counter(r["run_id"] for r in ok).items() if v > 1]
    if dupes:
        raise SystemExit(f"REFUSING ANALYSIS: duplicate successful run_ids, e.g. {dupes[:5]}")
    if errors:
        raise SystemExit(f"REFUSING ANALYSIS: canonical result file contains {len(errors)} error row(s)")

    by = {(r["case_id"], r["arm"], r["condition"]): r for r in ok}
    cases = sorted(set(r["case_id"] for r in ok))
    complete = [
        c for c in cases
        if all((c, "sequential", cond) in by for cond in CONDS)
        and (c, "fresh", "H_L4") in by
    ]
    if not args.allow_incomplete and len(complete) != args.expected_cases:
        raise SystemExit(
            f"REFUSING PARTIAL ANALYSIS: {len(complete)}/{args.expected_cases} complete cases. "
            "Run only after the main experiment is complete."
        )

    out = {
        "analysis_status": "complete" if len(complete) == args.expected_cases else "INCOMPLETE_EXPLORATORY",
        "n_complete_cases": len(complete),
        "n_success_rows": len(ok),
        "expected_success_rows": args.expected_cases * 6,
    }

    term = [(c, by[c, "sequential", "H_L4"], by[c, "fresh", "H_L4"]) for c in complete]
    n = len(term)
    agree = sum(s["decision"] == f["decision"] for _, s, f in term)
    dis = n - agree
    dc = [float(s["confidence"]) - float(f["confidence"]) for _, s, f in term]
    ci = bootstrap_mean_ci(dc, B=args.bootstrap, seed=20260922) if dc else [None, None]
    inc = lambda r: "E0" in r.get("dominant_evidence_ids", [])

    out["terminal"] = {
        "decision_agreement_n": agree,
        "decision_agreement_rate": agree / n if n else None,
        "decision_disagreement_n": dis,
        "decision_disagreement_rate": dis / n if n else None,
        "disagreement_95ci_clopper_pearson": clopper_pearson(dis, n),
        "confidence_seq_minus_fresh_mean": sum(dc) / n if n else None,
        "confidence_median": median(dc),
        "confidence_95ci_paired_bootstrap": ci,
        "confidence_lower_equal_higher": [
            sum(x < 0 for x in dc),
            sum(x == 0 for x in dc),
            sum(x > 0 for x in dc),
        ],
        "E0_transitions_fresh_to_sequential": dict(
            Counter(f"{inc(f)}->{inc(s)}" for _, s, f in term)
        ),
    }
    if n:
        out["terminal"]["accuracy_mcnemar"] = mcnemar_exact(
            [s["decision"] == s["reference_decision"] for _, s, f in term],
            [f["decision"] == f["reference_decision"] for _, s, f in term],
        )

    if complete:
        matrix = [[float(by[c, "sequential", cond]["confidence"]) for cond in CONDS] for c in complete]
        turn_means = [sum(row[j] for row in matrix) / len(matrix) for j in range(len(CONDS))]
        changes = [turn_means[j] - turn_means[0] for j in range(len(CONDS))]
        fully_noninc = sum(all(row[j] <= row[j-1] for j in range(1, len(row))) for row in matrix)
        terminal_le = sum(row[-1] <= row[0] for row in matrix)
        first_declines = Counter()
        first_decdev = Counter()
        e0_rates = []
        for j, cond in enumerate(CONDS):
            e0_rates.append(sum("E0" in by[c, "sequential", cond].get("dominant_evidence_ids", []) for c in complete) / len(complete))
        for c, row in zip(complete, matrix):
            fd = "none"
            for j in range(1, len(row)):
                if row[j] < row[j-1]:
                    fd = CONDS[j]
                    break
            first_declines[fd] += 1
            initial = by[c, "sequential", "H"]["decision"]
            dd = "none"
            for cond in CONDS[1:]:
                if by[c, "sequential", cond]["decision"] != initial:
                    dd = cond
                    break
            first_decdev[dd] += 1

        out["sequential_trajectory"] = {
            "conditions": CONDS,
            "turn_means": turn_means,
            "mean_change_from_initial": changes,
            "fully_nonincreasing_n": fully_noninc,
            "fully_nonincreasing_rate": fully_noninc / len(complete),
            "terminal_le_initial_n": terminal_le,
            "terminal_le_initial_rate": terminal_le / len(complete),
            "first_confidence_decline": dict(first_declines),
            "first_categorical_deviation": dict(first_decdev),
            "E0_inclusion_rate_by_turn": e0_rates,
        }

        threshold = {}
        for tau in range(70, 96):
            discord = sum(
                ((float(s["confidence"]) >= tau) != (float(f["confidence"]) >= tau))
                for _, s, f in term
            )
            seq_high_fresh_low = sum(
                (float(s["confidence"]) >= tau) and (float(f["confidence"]) < tau)
                for _, s, f in term
            )
            fresh_high_seq_low = sum(
                (float(f["confidence"]) >= tau) and (float(s["confidence"]) < tau)
                for _, s, f in term
            )
            threshold[str(tau)] = {
                "disagreement_n": discord,
                "disagreement_rate": discord / n,
                "sequential_ge_fresh_lt_n": seq_high_fresh_low,
                "fresh_ge_sequential_lt_n": fresh_high_seq_low,
            }
        out["exploratory_threshold_sensitivity"] = threshold

        strata = {}
        for keyfn, label in [
            (lambda r: r.get("reference_decision"), "reference_decision"),
        ]:
            vals = {}
            for _, s, f in term:
                key = str(keyfn(s))
                vals.setdefault(key, []).append(float(s["confidence"]) - float(f["confidence"]))
            strata[label] = {
                k: {"n": len(v), "mean_seq_minus_fresh": sum(v)/len(v), "median": median(v)}
                for k, v in vals.items()
            }
        out["secondary_stratified"] = strata

    text = json.dumps(out, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
