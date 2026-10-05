#!/usr/bin/env python3
"""RECONSTRUCTED GENERATOR — NOT ORIGINAL HISTORICAL SOURCE.

The script that produced
experiments/static_conflict/historical_package/evidence_not_vote_starter/
analysis/canonical_results_reference.md was not recovered (see
docs/canonical_reference_reconstruction.md). This is a NEW script, written
during Phase 4, that re-derives the same rounded reference text from the
archived (and Phase-3-reproduced) post-hoc and prespecified CSVs.

It reads the historical package READ-ONLY and never writes into it. Every
value is read from CSVs; none is typed by hand. Rounding is ROUND_HALF_UP
to the precision stated in the archived file's own header (2 decimals for
percentages/means/CIs, 1 decimal for medians), exactly as that header
describes.

The *order* of cohorts within sections 1, 2 and 7 is NOT derivable from any
recovered manifest or script (COHORTS in posthoc_contrasts.py iterates in a
different order for section-1-equivalent data than the archived file's
cohort order). Those three orders were therefore read off the archived
file's existing structure and hardcoded below as a PRESENTATION choice
(see docs/canonical_reference_reconstruction.md) -- they affect line
sequence only, never a computed value.

Usage:
    python scripts/reconstructed/build_canonical_results_reference.py
Writes (does not overwrite the archive):
    validation/reconstructed_reference/canonical_results_reference.md
"""
import argparse
import csv
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter"
POSTHOC = PKG / "analysis/posthoc_contrasts"
DEFAULT_OUT = ROOT / "validation/reconstructed_reference/canonical_results_reference.md"

CONDITIONS = ["H", "H_L1", "H_L2", "H_L4", "H_L4_ALIGNED", "L4_H"]
# Presentation order only (see module docstring); not a scientific value.
SECTION1_ORDER = ["primary", "replication", "gpt_oss_primary", "latent_v2", "veto", "gpt_oss_veto"]
SECTION2_ORDER = ["primary", "replication", "latent_v2", "gpt_oss_primary", "veto", "gpt_oss_veto"]
SECTION7_ORDER = ["primary", "replication", "latent_v2", "veto", "gpt_oss_primary"]
MODEL_LABEL = {"primary": "gemini-3.6-flash", "replication": "gemini-3.6-flash", "latent_v2": "gemini-3.6-flash",
               "veto": "gemini-3.6-flash", "gpt_oss_primary": "openai/gpt-oss-120b", "gpt_oss_veto": "openai/gpt-oss-120b"}
FOLDER = {"primary": "primary_gemini", "replication": "replication_gemini", "latent_v2": "latent_v2_gemini",
          "veto": "veto_gemini", "gpt_oss_primary": "gpt_oss_primary", "gpt_oss_veto": "gpt_oss_veto"}


def rd(name, where=POSTHOC):
    return list(csv.DictReader(open(where / name, encoding="utf-8")))


def r(x, places="0.01"):
    """ROUND_HALF_UP to the given decimal precision, as stated in the archived
    file's own header ('Rounded to two decimals with ROUND_HALF_UP')."""
    return Decimal(repr(float(x))).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def signed(x, places="0.01"):
    d = r(x, places)
    return f"+{d}" if d >= 0 else str(d)


def build():
    props = rd("binomial_proportions_exact.csv")
    by_cm = {}
    for row in props:
        by_cm.setdefault(row["cohort"], {})[row["metric"]] = row
    contrasts = {}
    for row in rd("confidence_contrasts_bootstrap.csv"):
        contrasts.setdefault(row["cohort"], {})[row["contrast"]] = row
    directions = {}
    for row in rd("confidence_direction_counts.csv"):
        directions.setdefault(row["cohort"], {})[row["contrast"]] = row
    strat_rows = rd("replication_conflict_aligned_by_stratum.csv")
    degr_rows = rd("categorical_degradation_summary.csv")
    mcnemar_rows = rd("paired_accuracy_mcnemar.csv")
    anon_rows = rd("anonymization_sensitivity.csv")

    out = []
    out += ["# Canonical results reference", "",
            "Rounded to two decimals with ROUND_HALF_UP (half away from zero), matching the",
            "manuscript convention. Full precision lives in the CSVs. Every number in the",
            "paper must match this file; do not recompute in drafting or plotting code.", "",
            "## 1. Categorical (exact Clopper-Pearson 95% CI)", ""]

    for cohort in SECTION1_ORDER:
        out.append(f"### {cohort} ({MODEL_LABEL[cohort]})")
        rows = by_cm[cohort]
        metrics = [f"accuracy_{c}" for c in CONDITIONS] + ["EDR1", "EDR2", "EDR4", "order_disagreement"]
        if cohort in ("veto", "gpt_oss_veto"):
            metrics += [f"VFR_{c}" for c in CONDITIONS]
        for m in metrics:
            row = rows[m]
            out.append(f"  {m.ljust(23)}{row['numerator']}/{row['denominator']} = "
                      f"{r(row['percent']):.2f}% [{r(row['cp_lo']):.2f}, {r(row['cp_hi']):.2f}]")
        out.append("")

    out.append("## 2. Confidence contrasts (paired bootstrap, 10,000, seed 68020260909)")
    out.append("")
    for cohort in SECTION2_ORDER:
        out.append(f"### {cohort}")
        for contrast in ("conflict_minus_H", "aligned_minus_H", "conflict_minus_aligned"):
            c = contrasts[cohort][contrast]
            d = directions[cohort][contrast]
            out.append(f"  {contrast.ljust(25)}{signed(c['mean_difference'])} "
                      f"[{signed(c['boot_lo'])}, {signed(c['boot_hi'])}]  n={c['n_cases']}  "
                      f"means {r(c['mean_a']):.2f} vs {r(c['mean_b']):.2f}  "
                      f"down/eq/up {d['n_decrease']}/{d['n_unchanged']}/{d['n_increase']}  "
                      f"median {signed(d['median_difference'], '0.1')}")
        out.append("")

    out.append("## 3. Stratified conflict-vs-aligned (Gemini replication, post-hoc)")
    out.append("")
    for row in strat_rows:
        out.append(f"  {row['stratum'].ljust(29)}n={int(row['n']):>3}  "
                  f"{signed(row['mean_conflict_minus_aligned'])} [{signed(row['ci_lo'])}, {signed(row['ci_hi'])}]  "
                  f"{row['conflict_lower']}/{row['equal']}/{row['conflict_higher']}  "
                  f"median {signed(row['median_difference'], '0.1')}")
    out.append("")

    out.append("## 4. Degradation (conditioned on H correct)")
    out.append("")
    for row in degr_rows:
        out.append(f"  {row['cohort'].ljust(17)}{row['contrast'].ljust(10)}"
                  f"denom={int(row['H_correct_denominator']):>3} total={row['categorical_degradation_total']} "
                  f"to_insufficient={row['to_insufficient']} wrong_direction={row['wrong_direction_reversal']} "
                  f"other={row['other_change']}")
    out.append("")

    out.append("## 5. McNemar exact")
    out.append("")
    for row in mcnemar_rows:
        out.append(f"  {row['cohort'].ljust(17)}{row['comparison'].ljust(23)}p={r(row['mcnemar_exact_p'], '0.001')}")
    out.append("")

    out.append("## 6. Anonymization sensitivity")
    out.append("")
    for row in anon_rows:
        if row["subset"] == "excluded case ids":
            out.append(f"  excluded ({row['n']}): {row['case_ids']}")
        else:
            out.append(f"  {row['subset'].ljust(47)}n={int(row['n']):>3}  "
                      f"{signed(row['mean_conflict_minus_aligned'])} [{signed(row['ci_lo'])}, {signed(row['ci_hi'])}]")
    out.append("")

    out.append("## 7. Flip threshold (PRESPECIFIED, score_results.py)")
    out.append("")
    import collections
    for cohort in SECTION7_ORDER:
        ft = rd("flip_threshold.csv", where=PKG / "analysis" / FOLDER[cohort])
        counts = dict(collections.Counter(row["flip_threshold"] for row in ft))
        out.append(f"  {cohort.ljust(17)}n={len(ft):>3}  {counts!r}")

    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None,
                    help="Override the output file path (default: "
                         "validation/reconstructed_reference/canonical_results_reference.md inside the "
                         "repo). Used by scripts/validate_public_release.py to write into a scratch/temp "
                         "location instead of modifying the checkout during validation.")
    args = ap.parse_args()
    out = Path(args.out) if args.out else DEFAULT_OUT

    text = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
