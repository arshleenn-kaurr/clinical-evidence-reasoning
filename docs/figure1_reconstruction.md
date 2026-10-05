# Figure 1 reconstruction (Phase 4, step 5)

**Status: DATA_EXACT / PLOT_RECONSTRUCTED**

- Original plotting code: **missing** (not recovered in any package; see `docs/figure_reproduction_status.md`).
- Underlying numerical data: **reproduced exactly** in Phase 3 (`posthoc_contrasts.py` re-run byte-for-byte under scipy 1.16.3).
- Plotting code: **newly reconstructed in Phase 4**. This is new code, not historical source. It is clearly labeled `RECONSTRUCTED PLOTTING CODE — NOT ORIGINAL HISTORICAL SOURCE` in its header and footer text.

## Source analysis files used (read-only)

`experiments/static_conflict/historical_package/evidence_not_vote_starter/analysis/posthoc_contrasts/`:
- `binomial_proportions_exact.csv` (Panel A: EDR1/EDR2/EDR4, cohorts `replication` and `gpt_oss_primary`)
- `confidence_contrasts_bootstrap.csv` + `confidence_direction_counts.csv` (Panel B: `conflict_minus_aligned` contrast, same two cohorts)

Every number plotted is read programmatically from these CSVs — none is typed by hand or adjusted to match the archived figure.

## Reconstructed code and output

- Code: `scripts/reconstructed/plot_genai4health_figure1.py`
- Output (does not overwrite the archive): `validation/reconstructed_figures/figure1_decision_confidence_dissociation_RECONSTRUCTED.{png,pdf}`

## Comparison with the archived figure

| Aspect | Archived (`figures/figure1_decision_confidence_dissociation.png`) | Reconstructed |
|---|---|---|
| Panel count/layout | 2 panels, side by side | same |
| Panel A title | "A  Categorical decisions remained stable" | same text |
| Panel B title | "B  Conflict reduced reported confidence" | same text |
| Panel A series | Gemini replication (n=260, blue circle, solid); GPT-OSS primary (n=40, orange square, dashed) | same |
| Panel A x-axis | Conflicting lower-tier evidence items (1, 2, 4) | same |
| Panel A y-axis | Evidence dilution rate (%) | same |
| Panel A annotations | numerator/denominator at each point | same (`2/259`, `1/259`, `1/259`, `0/40` ×3) |
| Panel A error bars | exact 95% Clopper-Pearson | same, from `binomial_proportions_exact.csv` |
| Panel B x-axis | Conflict − aligned self-reported confidence (points; paired mean difference), dashed reference line at 0 | same |
| Panel B annotations | Δ with 95% CI and lower/equal/higher counts, per cohort | same text/values |
| Panel B error bars | paired case-level bootstrap 95% CI | same, from `confidence_contrasts_bootstrap.csv` |
| Footnote | "Error bars: exact 95% Clopper-Pearson intervals (A); paired case-level bootstrap 95% CIs (B). Confidence is model-reported, not a calibrated probability." | identical text, plus an added RECONSTRUCTED disclosure line |

## Do all plotted numerical values match the archived figure?

**Yes**, per the manual reading of every annotation visible in the archived PNG against the reconstructed one:

| Value | Archived | Reconstructed |
|---|---|---|
| EDR1 (Gemini replication) | 2/259, point ≈0.8%, CI to ≈2.8 | 2/259, 0.77% [0.09, 2.76] |
| EDR2 (Gemini replication) | 1/259, point ≈0.4% | 1/259, 0.39% [0.01, 2.13] |
| EDR4 (Gemini replication) | 1/259, point ≈0.4%, CI to ≈8.8 | 1/259, 0.39% [0.01, 2.13] |
| EDR1/2/4 (GPT-OSS primary) | 0/40 at each dose | 0/40, 0.00% [0.00, 8.81] (×3) |
| Δ Gemini replication | −6.51 [−7.07, −5.95], 224/27/9 | identical |
| Δ GPT-OSS primary | −5.75 [−7.45, −3.60], 35/4/1 | identical |

## Visual differences (cosmetic, not scientific)

- Font, exact marker sizing, and figure proportions differ slightly (Matplotlib default theme vs. the archive's, which likely used custom rcParams).
- The archived Panel A plots whisker caps at some points that look slightly different in style; the reconstruction uses standard `errorbar` caps.
- The reconstruction adds an explicit "RECONSTRUCTED PLOTTING CODE" disclosure line in the footer; the archive does not have this (it is original).
- No attempt was made to match the archive pixel-for-pixel — only the panel structure, labels, displayed statistics, and qualitative layout, as instructed.

## What was not done

- No scientific value was altered to visually match the archive.
- The archived figure files were not overwritten, moved, or deleted.
- The reconstructed script is not presented anywhere as historical execution code (see its own header and `docs/limitations.md`).
