# Figure 1 reproduction status (Phase 3, step 10)

**Status: DATA_REPRODUCED / PLOTTING_CODE_MISSING**

Artifact: `experiments/static_conflict/historical_package/evidence_not_vote_starter/figures/figure1_decision_confidence_dissociation.{pdf,png}` (mtime 2026-09-09 19:16; PDF creator Matplotlib 3.10.9).

| Panel | Content (from figure) | Reproduced data source |
|---|---|---|
| A | EDR at 1/2/4 conflicting items with exact Clopper-Pearson 95% CI, Gemini replication (n=260) and GPT-OSS primary (n=40) | `binomial_proportions_exact.csv` rows `replication`/`gpt_oss_primary` × `EDR1/2/4` |
| B | Conflict − aligned confidence, paired bootstrap 95% CI, with lower/equal/higher counts | `confidence_contrasts_bootstrap.csv` + `confidence_direction_counts.csv`, `conflict_minus_aligned` |

The plotted values, extracted by script from the regenerated outputs, are in `validation/genai4health/figure1_data_from_reproduced_outputs.csv`. On visual inspection, every numeric annotation printed on the figure (EDR counts per dose, both Δ estimates with CIs, both direction-count triples) agrees with that table.

Not established: marker and error-bar positions were not measured, and the figure (19:16) predates the archived post-hoc CSVs (19:24), so its plotting code may have computed the values independently. No plotting code was recovered, and no figure was re-drawn.
