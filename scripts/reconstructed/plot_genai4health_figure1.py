#!/usr/bin/env python3
"""RECONSTRUCTED PLOTTING CODE — NOT ORIGINAL HISTORICAL SOURCE.

The script that produced
experiments/static_conflict/historical_package/evidence_not_vote_starter/
figures/figure1_decision_confidence_dissociation.{pdf,png} was not recovered
(see docs/figure_reproduction_status.md). This is a NEW script, written
during Phase 4, that re-draws the same two panels from the archived (and
Phase-3-reproduced) post-hoc CSVs. It reads the historical package
READ-ONLY and never writes into it.

Panel A: Evidence Dilution Rate at 1/2/4 conflicting items, with exact
         Clopper-Pearson 95% CIs, for Gemini replication (n=260) and
         GPT-OSS primary (n=40).
Panel B: Conflict-minus-aligned self-reported confidence, paired
         case-level bootstrap 95% CI, same two cohorts.

Data source: archived
  analysis/posthoc_contrasts/binomial_proportions_exact.csv
  analysis/posthoc_contrasts/confidence_contrasts_bootstrap.csv
  analysis/posthoc_contrasts/confidence_direction_counts.csv
No numerical value is invented, typed by hand, or adjusted to match the
archived figure; every number plotted is read from these CSVs.

Usage:
    python scripts/reconstructed/plot_genai4health_figure1.py
Writes (does not overwrite the archived figure):
    validation/reconstructed_figures/figure1_decision_confidence_dissociation_RECONSTRUCTED.png
    validation/reconstructed_figures/figure1_decision_confidence_dissociation_RECONSTRUCTED.pdf
"""
import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
POSTHOC = ROOT / "experiments/static_conflict/historical_package/evidence_not_vote_starter/analysis/posthoc_contrasts"
DEFAULT_OUT_DIR = ROOT / "validation/reconstructed_figures"

SERIES = [
    ("replication", "Gemini replication (n=260)", "#1f6fb4", "o", "-"),
    ("gpt_oss_primary", "GPT-OSS primary (n=40)", "#e07b1a", "s", "--"),
]


def rd(name):
    return list(csv.DictReader(open(POSTHOC / name, encoding="utf-8")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=None,
                    help="Override the output directory (default: validation/reconstructed_figures/ "
                         "inside the repo). Used by scripts/validate_public_release.py to write into a "
                         "scratch/temp location instead of modifying the checkout during validation.")
    args = ap.parse_args()
    out_dir = Path(args.out_dir) if args.out_dir else DEFAULT_OUT_DIR

    props = rd("binomial_proportions_exact.csv")
    contrasts = {(r["cohort"], r["contrast"]): r for r in rd("confidence_contrasts_bootstrap.csv")}
    directions = {(r["cohort"], r["contrast"]): r for r in rd("confidence_direction_counts.csv")}

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(13, 5.2))

    # ---- Panel A: EDR at 1/2/4 conflicting items ----
    xs = {"EDR1": 1, "EDR2": 2, "EDR4": 4}
    for cohort, label, color, marker, ls in SERIES:
        rows = {r["metric"]: r for r in props if r["cohort"] == cohort and r["metric"] in xs}
        x = [xs[m] for m in ("EDR1", "EDR2", "EDR4")]
        y = [float(rows[m]["percent"]) for m in ("EDR1", "EDR2", "EDR4")]
        lo = [float(rows[m]["percent"]) - float(rows[m]["cp_lo"]) for m in ("EDR1", "EDR2", "EDR4")]
        hi = [float(rows[m]["cp_hi"]) - float(rows[m]["percent"]) for m in ("EDR1", "EDR2", "EDR4")]
        axA.errorbar(x, y, yerr=[lo, hi], fmt=marker, color=color, linestyle=ls,
                    label=label, capsize=4, markersize=8, linewidth=1.8)
        for m, xx in zip(("EDR1", "EDR2", "EDR4"), x):
            r = rows[m]
            axA.annotate(f"{r['numerator']}/{r['denominator']}", (xx, float(r["percent"])),
                        textcoords="offset points", xytext=(-4, 8), fontsize=9)
    axA.set_xticks([1, 2, 4])
    axA.set_xlabel("Conflicting lower-tier evidence items")
    axA.set_ylabel("Evidence dilution rate (%)")
    axA.set_title("A   Categorical decisions remained stable", loc="left", fontweight="bold")
    axA.set_ylim(bottom=0)
    axA.legend(loc="upper right", frameon=False)

    # ---- Panel B: conflict - aligned confidence ----
    labels, means, los, his, annots = [], [], [], [], []
    for cohort, label, color, marker, ls in SERIES:
        c = contrasts[(cohort, "conflict_minus_aligned")]
        d = directions[(cohort, "conflict_minus_aligned")]
        labels.append(label)
        means.append(float(c["mean_difference"]))
        los.append(float(c["mean_difference"]) - float(c["boot_lo"]))
        his.append(float(c["boot_hi"]) - float(c["mean_difference"]))
        annots.append((float(c["mean_difference"]), float(c["boot_lo"]), float(c["boot_hi"]),
                       int(d["n_decrease"]), int(d["n_unchanged"]), int(d["n_increase"])))
    ypos = list(range(len(labels)))[::-1]
    colors = [s[2] for s in SERIES]
    for (m, lo, hi, dn, eq, up), y, color in zip(annots, ypos, colors):
        axB.errorbar([m], [y], xerr=[[m - lo], [hi - m]], fmt="o", color=color,
                    capsize=5, markersize=9, linewidth=1.8)
        axB.text(m, y - 0.28,
                 f"Δ = {m:.2f}  [{lo:.2f}, {hi:.2f}]\n{dn} lower / {eq} equal / {up} higher",
                 ha="center", va="top", fontsize=9)
    axB.axvline(0, color="#9ec6e3", linestyle="--", linewidth=1)
    axB.set_yticks(ypos)
    axB.set_yticklabels(labels)
    axB.set_xlabel("Conflict - aligned self-reported confidence\n(points; paired mean difference)")
    axB.set_title("B   Conflict reduced reported confidence", loc="left", fontweight="bold")
    axB.set_ylim(-0.8, max(ypos) + 0.8)

    fig.text(0.01, 0.01,
             "Error bars: exact 95% Clopper-Pearson intervals (A); paired case-level bootstrap 95% CIs (B). "
             "Confidence is model-reported, not a calibrated probability.\n"
             "RECONSTRUCTED PLOTTING CODE (Phase 4) — original historical plotting code not recovered. "
             "Data: posthoc_contrasts.py archived outputs, reproduced byte-exact in Phase 3.",
             fontsize=7.5, color="#555555")
    fig.suptitle("")
    fig.tight_layout(rect=(0, 0.06, 1, 1))

    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / "figure1_decision_confidence_dissociation_RECONSTRUCTED.png"
    pdf = out_dir / "figure1_decision_confidence_dissociation_RECONSTRUCTED.pdf"
    fig.savefig(png, dpi=200)
    fig.savefig(pdf)
    print(f"wrote {png}")
    print(f"wrote {pdf}")


if __name__ == "__main__":
    main()
