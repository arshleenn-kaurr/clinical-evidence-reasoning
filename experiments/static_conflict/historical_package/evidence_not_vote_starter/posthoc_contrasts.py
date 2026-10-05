#!/usr/bin/env python3
"""
posthoc_contrasts.py

Standalone, reproducible post-hoc analysis for the
"Evidence Is Not a Vote" benchmark.

WHY THIS FILE EXISTS
--------------------
Two families of numbers reported in the manuscript were not produced by
score_results.py:

  (1) Exact (Clopper-Pearson) confidence intervals for every binomial
      proportion we report. score_results.py reports percentile-bootstrap
      intervals on binary vectors, which degenerate at rates near 0 or 1
      (e.g. it returns [0, 0] for the veto failure rate 0/15, and a zero
      lower bound for EDR_1 = 2/259 despite two observed events).

  (2) The matched confidence contrasts between the H+4 conflict and
      H+4 aligned conditions. These were originally computed in an
      ad-hoc scratch session and were never archived. They are POST-HOC:
      analysis_contract.md v0 prespecifies EDR_4 as the primary endpoint
      and lists "confidence shift" (H -> H_L4) and "aligned-control delta"
      (an ACCURACY delta) as secondary endpoints. The conflict-vs-aligned
      CONFIDENCE contrast is a derived quantity that appears nowhere in
      the contract and must be labeled post-hoc in the manuscript.

DETERMINISM
-----------
Bootstrap seed is 68020260909, the bootstrap seed fixed in
analysis_contract.md v0. Percentile-bootstrap output depends on the order
of the resampled array, so every per-case vector is sorted by case_id
before resampling. This makes the intervals reproducible across runs and
machines, which the original merge-order-dependent numbers were not.

Point estimates are unchanged by the seed; only interval endpoints move.

USAGE
-----
    python3 posthoc_contrasts.py

Writes CSVs to analysis/posthoc_contrasts/ and a manifest with input and
output SHA256 digests.
"""

import collections
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path

import re

import numpy as np
import pandas as pd
from scipy import stats as st

# Bootstrap seed fixed in analysis_contract.md v0.
BOOT_SEED = 68020260909
N_BOOT = 10000

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "analysis" / "posthoc_contrasts"

CONDITIONS = ["H", "H_L1", "H_L2", "H_L4", "H_L4_ALIGNED", "L4_H"]

DIRECTIONAL = {"support", "do_not_support"}

# Anchor evidence quality is not carried in the frozen case files; it lives in
# the audit CSVs and is joined by case_id on the "evidence-quality" column.
AUDIT_QUALITY_SOURCE = {
    "data/final_main_cases.jsonl": "data/cochrane_candidates_audited.csv",
    "data/replication_cases.jsonl": "data/replication_candidates_audited.csv",
}

# Scope of the two descriptive post-hoc analyses.
ANONYMIZATION_COHORT = "replication"
ANONYMIZATION_PROMPTS = "data/replication_prompts.jsonl"

# A question is treated as retaining intervention-identifying terminology if it
# does not use the anonymized placeholder, or if a residual drug-name token
# survives anonymization. Derived by rule rather than hardcoded so the set is
# auditable from the frozen prompts.
DRUG_TOKEN = re.compile(
    r"\b\w{4,}(?:mab|nib|prazole|statin|cillin|mycin|olol|sartan|pril"
    r"|azepam|caine|vir|ximab|zumab)\b", re.I
)


def identifying_case_ids(prompts_rel):
    ids = set()
    for r in read_jsonl(ROOT / prompts_rel):
        if r["condition"] != "H":
            continue
        q = r["question"]
        if "Intervention A" not in q or DRUG_TOKEN.search(q):
            ids.add(r["case_id"])
    return ids


STRATIFIED_COHORT = "replication"
TRANSITION_COHORTS = ("replication", "gpt_oss_primary")

# Prespecification status recorded per output file. Nothing here is a contract
# endpoint: "post_hoc" marks an inferential analysis (bootstrap intervals),
# "post_hoc_descriptive" marks pure counts with no interval or test.
OUTPUT_STATUS = {
    "binomial_proportions_exact.csv": "post_hoc",
    "confidence_contrasts_bootstrap.csv": "post_hoc",
    "confidence_direction_counts.csv": "post_hoc_descriptive",
    "paired_accuracy_mcnemar.csv": "post_hoc",
    "replication_conflict_aligned_by_stratum.csv": "post_hoc",
    "categorical_transition_matrix.csv": "post_hoc_descriptive",
    "anonymization_sensitivity.csv": "post_hoc",
    "categorical_degradation_summary.csv": "post_hoc_descriptive",
}


def load_quality(cases_rel):
    """case_id -> anchor evidence quality, or {} when no audit source exists."""
    src = AUDIT_QUALITY_SOURCE.get(cases_rel)
    if src is None:
        return {}
    with open(ROOT / src, encoding="utf-8", newline="") as f:
        return {r["case_id"]: r["evidence-quality"] for r in csv.DictReader(f)}

# (cohort label, results file, cases file, model)
#
# gpt_oss_primary is a SECOND-MODEL SENSITIVITY ANALYSIS on the same frozen
# 40-case primary cohort and the same frozen prompts. It is NOT an independent
# cohort replication: it reuses primary cases, adds no new clinical cases, and
# was run after the Gemini results were known.
COHORTS = [
    ("primary", "results/final_main_gemini_3_6_flash.jsonl",
     "data/final_main_cases.jsonl", "gemini-3.6-flash"),
    ("replication", "results/replication_gemini_3_6_flash_CLEAN.jsonl",
     "data/replication_cases.jsonl", "gemini-3.6-flash"),
    ("latent_v2", "results/latent_v2_main_gemini_3_6_flash_CLEAN.jsonl",
     "data/final_main_cases.jsonl", "gemini-3.6-flash"),
    ("veto", "results/final_veto_gemini_3_6_flash.jsonl",
     "data/final_veto_cases.jsonl", "gemini-3.6-flash"),
    ("gpt_oss_primary", "results/final_main_gpt_oss_120b_CLEAN.jsonl",
     "data/final_main_cases.jsonl", "openai/gpt-oss-120b"),
    ("gpt_oss_veto", "results/final_veto_gpt_oss_120b_CLEAN.jsonl",
     "data/final_veto_cases.jsonl", "openai/gpt-oss-120b"),
]


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clopper_pearson(k, n, alpha=0.05):
    """Exact binomial interval. Returns (proportion, lo, hi) as percentages."""
    if n == 0:
        return (float("nan"),) * 3
    lo = 0.0 if k == 0 else st.beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else st.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return 100.0 * k / n, 100.0 * lo, 100.0 * hi


def paired_bootstrap(diffs, seed=BOOT_SEED, n=N_BOOT):
    """Percentile bootstrap over CASE-LEVEL paired differences.

    `diffs` must already be ordered deterministically (sorted by case_id).
    """
    x = np.asarray(diffs, dtype=float)
    if x.size == 0:
        return (float("nan"),) * 3
    rng = np.random.default_rng(seed)
    boots = np.empty(n)
    for i in range(n):
        boots[i] = rng.choice(x, size=x.size, replace=True).mean()
    return float(x.mean()), float(np.quantile(boots, 0.025)), \
        float(np.quantile(boots, 0.975))


def mcnemar_exact(b, c):
    """Exact McNemar test on discordant pair counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    return float(st.binomtest(b, n, 0.5).pvalue)


def load_cohort(results_rel, cases_rel):
    res = pd.DataFrame(read_jsonl(ROOT / results_rel))
    cases = pd.DataFrame(read_jsonl(ROOT / cases_rel))
    key = cases[["case_id", "reference_decision"]]
    df = res.merge(key, on="case_id", how="left", suffixes=("", "_case"))
    if "reference_decision_case" in df.columns:
        df["reference_decision"] = (
            df["reference_decision_case"].fillna(df["reference_decision"])
        )
    df["correct"] = (df["decision"] == df["reference_decision"]).astype(int)
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")
    return df


def pivot(df, values):
    """Case x condition table, rows sorted by case_id for determinism."""
    p = df.pivot_table(index="case_id", columns="condition",
                       values=values, aggfunc="first")
    return p.sort_index()


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    prop_rows, conf_rows, dir_rows, paired_acc_rows = [], [], [], []
    strat_rows, trans_rows, degr_rows = [], [], []
    anon_rows = []

    for cohort, results_rel, cases_rel, model in COHORTS:
        df = load_cohort(results_rel, cases_rel)
        correct = pivot(df, "correct")
        conf = pivot(df, "confidence")
        decision = pivot(df, "decision")

        # ---- Condition accuracies: exact binomial ----
        for cond in CONDITIONS:
            if cond not in correct.columns:
                continue
            col = correct[cond].dropna()
            k, n = int(col.sum()), int(col.size)
            est, lo, hi = clopper_pearson(k, n)
            prop_rows.append({
                "cohort": cohort, "model": model, "metric": f"accuracy_{cond}",
                "numerator": k, "denominator": n, "percent": est,
                "cp_lo": lo, "cp_hi": hi,
            })

        # ---- EDR, conditional on H being correct ----
        base = correct[correct["H"] == 1]
        for cond, n_weak in [("H_L1", 1), ("H_L2", 2), ("H_L4", 4)]:
            if cond not in base.columns:
                continue
            flips = (base[cond] == 0).astype(int)
            k, n = int(flips.sum()), int(flips.size)
            est, lo, hi = clopper_pearson(k, n)
            prop_rows.append({
                "cohort": cohort, "model": model, "metric": f"EDR{n_weak}",
                "numerator": k, "denominator": n, "percent": est,
                "cp_lo": lo, "cp_hi": hi,
            })

        # ---- Order disagreement between H_L4 and L4_H ----
        if {"H_L4", "L4_H"} <= set(decision.columns):
            disagree = (decision["H_L4"] != decision["L4_H"]).astype(int)
            k, n = int(disagree.sum()), int(disagree.size)
            est, lo, hi = clopper_pearson(k, n)
            prop_rows.append({
                "cohort": cohort, "model": model, "metric": "order_disagreement",
                "numerator": k, "denominator": n, "percent": est,
                "cp_lo": lo, "cp_hi": hi,
            })

        # ---- Veto failure rate: support despite veto-class evidence ----
        if cases_rel.endswith("final_veto_cases.jsonl"):
            for cond in CONDITIONS:
                if cond not in decision.columns:
                    continue
                fail = (decision[cond] == "support").astype(int)
                k, n = int(fail.sum()), int(fail.size)
                est, lo, hi = clopper_pearson(k, n)
                prop_rows.append({
                    "cohort": cohort, "model": model, "metric": f"VFR_{cond}",
                    "numerator": k, "denominator": n, "percent": est,
                    "cp_lo": lo, "cp_hi": hi,
                })

        # ---- Paired accuracy comparisons: exact McNemar, not an interval ----
        # A Clopper-Pearson interval is NOT valid for a paired difference in
        # two accuracies. We report the discordant pair counts and an exact
        # McNemar p-value; the two marginal accuracies carry their own exact
        # intervals above.
        for a, b in [("H_L4_ALIGNED", "H_L4"), ("L4_H", "H_L4")]:
            if not {a, b} <= set(correct.columns):
                continue
            m = correct[[a, b]].dropna()
            b_only = int(((m[a] == 1) & (m[b] == 0)).sum())
            c_only = int(((m[a] == 0) & (m[b] == 1)).sum())
            paired_acc_rows.append({
                "cohort": cohort, "model": model, "comparison": f"{a}_vs_{b}", "n": len(m),
                "acc_a": float(m[a].mean()), "acc_b": float(m[b].mean()),
                f"n_correct_{a}_only": b_only,
                f"n_correct_{b}_only": c_only,
                "mcnemar_exact_p": mcnemar_exact(b_only, c_only),
            })

        # ---- Matched confidence contrasts: paired case-level bootstrap ----
        for a, b, label in [
            ("H_L4", "H", "conflict_minus_H"),
            ("H_L4_ALIGNED", "H", "aligned_minus_H"),
            ("H_L4", "H_L4_ALIGNED", "conflict_minus_aligned"),
        ]:
            if not {a, b} <= set(conf.columns):
                continue
            m = conf[[a, b]].dropna()
            diffs = (m[a] - m[b]).values
            est, lo, hi = paired_bootstrap(diffs)
            conf_rows.append({
                "cohort": cohort, "model": model, "contrast": label, "n_cases": len(m),
                "mean_a": float(m[a].mean()), "mean_b": float(m[b].mean()),
                "mean_difference": est, "boot_lo": lo, "boot_hi": hi,
                "boot_seed": BOOT_SEED, "n_boot": N_BOOT,
            })

            # Assumption-free companion: reported confidence is emitted on a
            # coarse lattice, so direction counts are reported alongside the
            # mean difference.
            down = int((diffs < 0).sum())
            same = int((diffs == 0).sum())
            up = int((diffs > 0).sum())
            nz = down + up
            dir_rows.append({
                "cohort": cohort, "model": model, "contrast": label, "n_cases": len(diffs),
                "n_decrease": down, "n_unchanged": same, "n_increase": up,
                "median_difference": float(np.median(diffs)),
                "sign_test_p": (
                    float(st.binomtest(down, nz, 0.5).pvalue)
                    if nz else float("nan")
                ),
            })

        # ---- Post-hoc stratified conflict-vs-aligned confidence contrast ----
        # Heterogeneity check across the frozen anchor-quality x reference-
        # decision strata. Not a contract endpoint and not prespecified.
        if cohort == STRATIFIED_COHORT:
            quality = load_quality(cases_rel)
            ref = df.groupby("case_id")["reference_decision"].first()
            matched = conf[["H_L4", "H_L4_ALIGNED"]].dropna()

            def stratum_row(label, ids, qual, refdec):
                sub = matched.loc[sorted(ids)]
                d = (sub["H_L4"] - sub["H_L4_ALIGNED"]).values
                est, lo, hi = paired_bootstrap(d)
                return {
                    "stratum": label, "evidence_quality": qual,
                    "reference_decision": refdec,
                    "cohort": cohort, "model": model, "n": len(d),
                    "mean_conflict_minus_aligned": est,
                    "ci_lo": lo, "ci_hi": hi,
                    "conflict_lower": int((d < 0).sum()),
                    "equal": int((d == 0).sum()),
                    "conflict_higher": int((d > 0).sum()),
                    "median_difference": float(np.median(d)),
                    "bootstrap_resamples": N_BOOT,
                    "bootstrap_seed": BOOT_SEED,
                    "prespecification_status": "post_hoc",
                }

            strat_rows.append(
                stratum_row("Overall", matched.index, "", "")
            )
            for qual in ("High", "Moderate"):
                for refdec in ("support", "do_not_support"):
                    ids = [
                        c for c in matched.index
                        if quality.get(c) == qual and ref[c] == refdec
                    ]
                    if ids:
                        strat_rows.append(
                            stratum_row(
                                f"{qual} / {refdec}", ids, qual, refdec
                            )
                        )

        # ---- Post-hoc anonymization sensitivity ----
        # Some replication questions retained intervention-identifying wording.
        # Recompute the matched conflict-vs-aligned contrast with those cases
        # removed. This does not address training-data exposure generally.
        if cohort == ANONYMIZATION_COHORT:
            leaked = identifying_case_ids(ANONYMIZATION_PROMPTS)
            matched_a = conf[["H_L4", "H_L4_ALIGNED"]].dropna()

            def anon_row(label, ids):
                sub = matched_a.loc[sorted(ids)]
                d = (sub["H_L4"] - sub["H_L4_ALIGNED"]).values
                est, lo, hi = paired_bootstrap(d)
                return {
                    "subset": label, "cohort": cohort, "model": model,
                    "n": len(d),
                    "mean_conflict_minus_aligned": est,
                    "ci_lo": lo, "ci_hi": hi,
                    "conflict_lower": int((d < 0).sum()),
                    "equal": int((d == 0).sum()),
                    "conflict_higher": int((d > 0).sum()),
                    "median_difference": float(np.median(d)),
                    "bootstrap_resamples": N_BOOT,
                    "bootstrap_seed": BOOT_SEED,
                    "prespecification_status": "post_hoc",
                }

            keep = [c for c in matched_a.index if c not in leaked]
            only = [c for c in matched_a.index if c in leaked]
            anon_rows.append(anon_row("all cases", matched_a.index))
            anon_rows.append(
                anon_row("excluding intervention-identifying questions", keep)
            )
            if only:
                anon_rows.append(
                    anon_row("intervention-identifying questions only", only)
                )
            anon_rows.append({
                "subset": "excluded case ids", "cohort": cohort,
                "model": model, "n": len(only),
                "mean_conflict_minus_aligned": float("nan"),
                "ci_lo": float("nan"), "ci_hi": float("nan"),
                "conflict_lower": -1, "equal": -1, "conflict_higher": -1,
                "median_difference": float("nan"),
                "bootstrap_resamples": N_BOOT, "bootstrap_seed": BOOT_SEED,
                "prespecification_status": "post_hoc",
                "case_ids": ";".join(sorted(only)),
            })

        # ---- Post-hoc categorical transition analysis ----
        # Where do decisions go when they degrade? Counts only, no intervals.
        if cohort in TRANSITION_COHORTS:
            base_ids = sorted(correct.index[correct["H"] == 1])
            for cond in ("H_L1", "H_L2", "H_L4"):
                pairs = collections.Counter()
                unchanged = 0
                to_insuff = reversal = other = 0
                for cid in base_ids:
                    frm = decision.loc[cid, "H"]
                    to = decision.loc[cid, cond]
                    pairs[(frm, to)] += 1
                    if int(correct.loc[cid, cond]) == 1:
                        unchanged += 1
                    elif to == "insufficient":
                        to_insuff += 1
                    elif frm in DIRECTIONAL and to in DIRECTIONAL and frm != to:
                        reversal += 1
                    else:
                        other += 1

                for (frm, to), n in sorted(pairs.items()):
                    trans_rows.append({
                        "cohort": cohort, "model": model,
                        "contrast": f"H->{cond}",
                        "from_decision": frm, "to_decision": to, "n": n,
                        "prespecification_status": "post_hoc_descriptive",
                    })

                degr_rows.append({
                    "cohort": cohort, "model": model,
                    "contrast": f"H->{cond}",
                    "H_correct_denominator": len(base_ids),
                    "unchanged_correct": unchanged,
                    "categorical_degradation_total":
                        to_insuff + reversal + other,
                    "to_insufficient": to_insuff,
                    "wrong_direction_reversal": reversal,
                    "other_change": other,
                    "prespecification_status": "post_hoc_descriptive",
                })

    outputs = {
        "replication_conflict_aligned_by_stratum.csv": pd.DataFrame(strat_rows),
        "categorical_transition_matrix.csv": pd.DataFrame(trans_rows),
        "anonymization_sensitivity.csv": pd.DataFrame(anon_rows),
        "categorical_degradation_summary.csv": pd.DataFrame(degr_rows),
        "binomial_proportions_exact.csv": pd.DataFrame(prop_rows),
        "confidence_contrasts_bootstrap.csv": pd.DataFrame(conf_rows),
        "confidence_direction_counts.csv": pd.DataFrame(dir_rows),
        "paired_accuracy_mcnemar.csv": pd.DataFrame(paired_acc_rows),
    }
    for name, frame in outputs.items():
        frame.to_csv(OUT / name, index=False)

    manifest = {
        "script": "posthoc_contrasts.py",
        "script_sha256": sha256(Path(__file__)),
        "bootstrap_seed": BOOT_SEED,
        "n_bootstrap": N_BOOT,
        "prespecification_status": (
            "POST-HOC. analysis_contract.md v0 prespecifies EDR_4 as the "
            "primary endpoint and lists 'confidence shift' (H -> H_L4) and "
            "'aligned-control delta' (accuracy) as secondary endpoints. The "
            "conflict-vs-aligned CONFIDENCE contrast is not a contract "
            "endpoint. Exact binomial intervals replace the degenerate "
            "percentile-bootstrap intervals emitted by score_results.py for "
            "binary proportions. The gpt_oss_primary rows are a post-hoc "
            "SECOND-MODEL SENSITIVITY ANALYSIS on the frozen 40-case primary "
            "cohort and frozen prompts, run after the Gemini results were "
            "known; they are not an independent cohort replication and add no "
            "new clinical cases. The veto and gpt_oss_veto cohorts are the SAME 15 "
            "AHA guideline cases evaluated by two models: they are 15 cases "
            "observed twice, not 30 independent cases. Veto failure rates and "
            "their exact intervals are reported per model and must not be "
            "pooled across models."
        ),
        "determinism_note": (
            "Per-case vectors are sorted by case_id before resampling so that "
            "interval endpoints do not depend on merge order."
        ),
        "inputs": {
            rel: sha256(ROOT / rel)
            for _, results_rel, cases_rel, _m in COHORTS
            for rel in (results_rel, cases_rel)
        },
        "outputs": {
            name: {
                "sha256": sha256(OUT / name),
                "prespecification_status": OUTPUT_STATUS[name],
            }
            for name in outputs
        },
    }
    with (OUT / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

    print(f"Wrote {len(outputs) + 1} files -> {OUT}")


if __name__ == "__main__":
    main()
