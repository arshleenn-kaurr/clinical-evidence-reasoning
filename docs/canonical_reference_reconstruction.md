# canonical_results_reference.md reconstruction (Phase 4, step 6)

**Status: EXACT_MATCH (byte-identical).**

- Generator: **missing** (no recovered script writes `analysis/canonical_results_reference.md`; see `docs/posthoc_hash_investigation.md`, which flags an unused `Decimal`/`ROUND_HALF_UP` import in `posthoc_contrasts.py` as a likely connection).
- Values: all 122 numeric lines verified against reproduced outputs in Phase 3.
- Generator code: **newly reconstructed in Phase 4** (`scripts/reconstructed/build_canonical_results_reference.py`), clearly labeled `RECONSTRUCTED GENERATOR — NOT ORIGINAL HISTORICAL SOURCE`.

## Result

```
$ python scripts/reconstructed/build_canonical_results_reference.py
$ diff validation/reconstructed_reference/canonical_results_reference.md \
       experiments/static_conflict/historical_package/evidence_not_vote_starter/analysis/canonical_results_reference.md
(no output)
```

Both files hash to `5ba79e1091fdbd4b8700c9b4eae26426d6f9066cb970a17f58bc23d235b7fc38`.

- **Scientific values:** identical (read programmatically from the archived, Phase-3-reproduced `posthoc_contrasts.py` and `score_results.py` outputs; none typed by hand).
- **Rounding rule:** identical — ROUND_HALF_UP, as the archived file's own header states, applied at 2 decimals for percentages/means/CIs and 1 decimal for medians.
- **Textual result lines:** identical, including column widths/padding.

## What had to be reverse-engineered vs. what was read from data

| Element | Source |
|---|---|
| All numeric values | Read from archived CSVs (`binomial_proportions_exact.csv`, `confidence_contrasts_bootstrap.csv`, `confidence_direction_counts.csv`, `replication_conflict_aligned_by_stratum.csv`, `categorical_degradation_summary.csv`, `paired_accuracy_mcnemar.csv`, `anonymization_sensitivity.csv`, and each cohort's prespecified `flip_threshold.csv`) |
| Row order within sections 3, 4, 5, 6 | Preserved directly from each archived CSV's row order (write order of the original analysis code) |
| Row order within sections 1, 2, 7 | **Not derivable from any recovered file** — the three section orders differ from each other and from the `COHORTS` list order in `posthoc_contrasts.py`. Measured directly off the archived `.md` text and hardcoded as `SECTION1_ORDER` / `SECTION2_ORDER` / `SECTION7_ORDER` constants. This is a **presentation choice** (which line comes first), not a computed value — it affects nothing numeric. |
| Column widths (e.g. metric name padded to 23 chars) | Measured directly off the archived `.md` text byte positions |
| Section 7's omission of `gpt_oss_veto` | Observed in the archive (only 5 of 6 cohorts appear) and reproduced as-is, not invented |

## Not done

The archived file was not overwritten, moved, or deleted. The reconstructed generator is documented here and in its own header as new Phase 4 code, never presented as historical.
